import streamlit as st
import gspread
import pandas as pd
import time
from oauth2client.service_account import ServiceAccountCredentials

# Cache para conectar Google Sheets (não cache o objeto client, só a função)
@st.cache_resource(ttl=600)
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
    client = gspread.authorize(creds)
    return client

# Cache para pegar dados dos perfis e likes (com TTL para atualizar a cada 10 minutos)
@st.cache_data(ttl=600)
def carregar_dados(client, planilha_nome="TINDER_CEO_PERFIS"):
    sheet = client.open(planilha_nome)
    perfis_ws = sheet.worksheet("perfis")
    try:
        likes_ws = sheet.worksheet("likes")
    except gspread.exceptions.WorksheetNotFound:
        likes_ws = sheet.add_worksheet(title="likes", rows="1000", cols="5")
        likes_ws.append_row(["quem_curtiu", "quem_foi_curtido"])
    perfis = perfis_ws.get_all_values()
    likes = likes_ws.get_all_records()
    return perfis, likes, perfis_ws, likes_ws

# Função para converter link Google Drive em URL direta
def drive_link_para_visualizacao(link):
    if "id=" in link:
        file_id = link.split("id=")[-1]
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return link

st.title("💘LIKES DA CEÓ")

usuario = st.text_input("Digite seu login privado")
if not usuario:
    st.stop()

client = conectar_google_sheets()
perfis, likes_raw, perfis_ws, likes_ws = carregar_dados(client)

if not perfis or len(perfis) < 2:
    st.warning("Nenhum perfil cadastrado ainda.")
    st.stop()

cabecalho, dados = perfis[0], perfis[1:]
df = pd.DataFrame(dados, columns=cabecalho).replace("", pd.NA).dropna(how="all")
df.columns = df.columns.str.strip()

if "login" not in df.columns:
    st.error("A aba 'perfis' precisa da coluna 'login'.")
    st.stop()

# Remove o próprio perfil para não aparecer para ele mesmo
df = df[df["login"] != usuario]

df_likes = pd.DataFrame(likes_raw) if likes_raw else pd.DataFrame(columns=["quem_curtiu", "quem_foi_curtido"])
df_likes.columns = df_likes.columns.str.strip()

if not set(["quem_curtiu", "quem_foi_curtido"]).issubset(df_likes.columns):
    st.error("A aba 'likes' precisa das colunas 'quem_curtiu' e 'quem_foi_curtido'.")
    st.stop()

# Lista de perfis já curtidos pelo usuário
ja_curtiu = df_likes[df_likes["quem_curtiu"] == usuario]["quem_foi_curtido"].tolist()
df_restantes = df[~df["login"].isin(ja_curtiu)]

# Estado para armazenar o perfil atual em exibição
if "perfil_atual" not in st.session_state:
    if df_restantes.empty:
        st.success("Você já viu todos os perfis disponíveis! Agora é só esperar os matches 🥰")
        st.stop()
    st.session_state.perfil_atual = df_restantes.sample(1).iloc[0].to_dict()

perfil = st.session_state.perfil_atual

st.subheader(perfil.get("nome_publico", "Nome não informado"))
st.text(perfil.get("descricao", ""))
st.markdown("🎵 **Músicas do set:**")
st.text(perfil.get("musicas", ""))

# Exibe as fotos
fotos = perfil.get("fotos", "")
if isinstance(fotos, str) and fotos.strip():
    lista_links = [link.strip() for link in fotos.split(",") if link.strip()]
    st.info("Fotos enviadas:")
    cols = st.columns(3)
    for i, link in enumerate(lista_links):
        img_url = drive_link_para_visualizacao(link)
        with cols[i % 3]:
            st.image(img_url, use_column_width=True)
else:
    st.write("Sem fotos para mostrar.")

# Botões Curtir e Pular
col1, col2 = st.columns(2)
with col1:
    if st.button("💖 Curtir"):
        # Recarrega likes atualizados para evitar duplicidade
        likes_atualizados = likes_ws.get_all_records()
        df_likes_atual = pd.DataFrame(likes_atualizados) if likes_atualizados else pd.DataFrame(columns=["quem_curtiu", "quem_foi_curtido"])
        df_likes_atual.columns = df_likes_atual.columns.str.strip()

        ja_curtiu_esse = not df_likes_atual[
            (df_likes_atual["quem_curtiu"] == usuario) & 
            (df_likes_atual["quem_foi_curtido"] == perfil["login"])
        ].empty

        if ja_curtiu_esse:
            st.warning("Você já curtiu esse perfil.")
        else:
            likes_ws.append_row([usuario, perfil["login"]])
            st.success("Curtida registrada com sucesso 💘")
            st.balloons()
            st.toast("Like enviado! Carregando o próximo perfil...", icon="💘")
            time.sleep(2)
            del st.session_state.perfil_atual
            st.experimental_rerun()

with col2:
    if st.button("⏩ Pular"):
        del st.session_state.perfil_atual
        st.experimental_rerun()
