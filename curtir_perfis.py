import streamlit as st
import gspread
import pandas as pd
import time
import random
from google.oauth2.service_account import Credentials

# Autenticação Google
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Nome da planilha
PLANILHA = "TINDER_CEO_PERFIS"

# Não usar cache, para evitar erro de reconexão
def carregar_sheet():
    for tentativa in range(3):
        try:
            return client.open(PLANILHA)
        except gspread.exceptions.APIError:
            if tentativa == 2:
                st.error("Erro ao conectar com o Google Sheets. Tente novamente em instantes.")
                st.stop()
            time.sleep(1.5)

sheet = carregar_sheet()

# Acessa aba "perfis"
try:
    perfis_ws = sheet.worksheet("perfis")
except Exception as e:
    st.error(f"Erro ao acessar aba 'perfis': {e}")
    st.stop()

# Acessa ou cria aba "likes"
try:
    likes_ws = sheet.worksheet("likes")
except gspread.exceptions.WorksheetNotFound:
    likes_ws = sheet.add_worksheet(title="likes", rows="1000", cols="5")
    likes_ws.append_row(["quem_curtiu", "quem_foi_curtido"])

# Converte link Drive para thumbnail
def drive_link_para_visualizacao(link):
    if "id=" in link:
        file_id = link.split("id=")[-1]
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    elif "export=view&id=" in link:
        file_id = link.split("id=")[-1]
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return link

# App
st.title("💘LIKES DA CEÓ")

usuario = st.text_input("Digite seu login privado")
if not usuario:
    st.stop()

valores = perfis_ws.get_all_values()
if not valores:
    st.warning("Nenhum perfil cadastrado ainda.")
    st.stop()

cabecalho, dados = valores[0], valores[1:]
df = pd.DataFrame(dados, columns=cabecalho)
df = df.replace("", pd.NA).dropna(how="all")
df.columns = df.columns.str.strip()

if "login" not in df.columns:
    st.error("A aba 'perfis' precisa da coluna 'login'.")
    st.stop()

df = df[df["login"] != usuario]

# Carrega curtidas
likes_data = likes_ws.get_all_records()
likes = pd.DataFrame(likes_data) if likes_data else pd.DataFrame(columns=["quem_curtiu", "quem_foi_curtido"])
likes.columns = [str(col).strip() for col in likes.columns]

if not set(["quem_curtiu", "quem_foi_curtido"]).issubset(likes.columns):
    st.error("A aba 'likes' precisa das colunas 'quem_curtiu' e 'quem_foi_curtido'.")
    st.stop()

ja_curtiu = likes[likes["quem_curtiu"] == usuario]["quem_foi_curtido"].tolist()
df_restantes = df[~df["login"].isin(ja_curtiu)]

if "perfil_atual" not in st.session_state:
    if df_restantes.empty:
        st.success("Você já viu todos os perfis disponíveis! Agora é só esperar os matches 🥰")
        st.stop()

    perfis_possiveis = df_restantes.to_dict("records")
    random.shuffle(perfis_possiveis)

    for p in perfis_possiveis:
        if not likes[
            (likes["quem_curtiu"] == usuario) & (likes["quem_foi_curtido"] == p["login"])
        ].empty:
            continue
        st.session_state.perfil_atual = p
        break
    else:
        st.success("Você já curtiu todos os perfis disponíveis!")
        st.stop()

perfil = st.session_state.perfil_atual

st.subheader(perfil.get("nome_publico", "Nome não informado"))
st.text(perfil.get("descricao", ""))
st.markdown("🎵 **Músicas do set:**")
st.text(perfil.get("musicas", ""))

fotos = perfil.get("fotos", "")
if isinstance(fotos, str) and fotos.strip():
    lista_links = [link.strip() for link in fotos.split(",") if link.strip()]
    st.info("Fotos enviadas:")
    cols = st.columns(3)
    for i, link in enumerate(lista_links):
        img_url = drive_link_para_visualizacao(link)
        with cols[i % 3]:
            st.markdown(
                f'<img src="{img_url}" style="width:100%; border-radius: 10px; margin-bottom:10px;">',
                unsafe_allow_html=True
            )
else:
    st.write("Sem fotos para mostrar.")

col1, col2 = st.columns(2)
with col1:
    if st.button("💖 Curtir"):
        likes_atualizados = likes_ws.get_all_records()
        
        if likes_atualizados:
            df_likes = pd.DataFrame(likes_atualizados)
        else:
            df_likes = pd.DataFrame(columns=["quem_curtiu", "quem_foi_curtido"])

        df_likes.columns = [str(col).strip() for col in df_likes.columns]

        ja_curtiu = (
            not df_likes[
                (df_likes["quem_curtiu"] == usuario) & 
                (df_likes["quem_foi_curtido"] == perfil["login"])
            ].empty
        )

        if ja_curtiu:
            st.warning("Você já curtiu esse perfil.")
        else:
            likes_ws.append_row([usuario, perfil["login"]])
            st.success("Curtida registrada com sucesso 💘")

        del st.session_state.perfil_atual
        st.rerun()

with col2:
    if st.button("⏩ Pular"):
        del st.session_state.perfil_atual
        st.rerun()
