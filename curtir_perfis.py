import streamlit as st
import gspread
import pandas as pd
import time
import random
from google.oauth2.service_account import Credentials

# Autenticação moderna com Google
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds_dict = st.secrets["gcp_service_account"]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(credentials)

PLANILHA = "TINDER_CEO_PERFIS"

# Função com retry para abrir a planilha
@st.cache_data(ttl=60)
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

# Abas
try:
    perfis_ws = sheet.worksheet("perfis")
except Exception as e:
    st.error(f"Erro ao acessar a aba 'perfis': {e}")
    st.stop()

try:
    likes_ws = sheet.worksheet("likes")
except gspread.exceptions.WorksheetNotFound:
    likes_ws = sheet.add_worksheet(title="likes", rows="1000", cols="5")
    likes_ws.append_row(["quem_curtiu", "quem_foi_curtido"])

# Função para visualizar imagem do Drive
def drive_link_para_visualizacao(link):
    if "id=" in link:
        file_id = link.split("id=")[-1]
    elif "export=view&id=" in link:
        file_id = link.split("id=")[-1]
    else:
        return link
    return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"

# Interface principal
st.title("💘LIKES DA CEÓ")
usuario = st.text_input("Digite seu login privado")
if not usuario:
    st.stop()

# Carrega perfis
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

df = df[df["login"] != usuario]  # remove o próprio perfil

# Carrega curtidas
likes_data = likes_ws.get_all_records()
likes = pd.DataFrame(likes_data) if likes_data else pd.DataFrame(columns=["quem_curtiu", "quem_foi_curtido"])
likes.columns = likes.columns.str.strip()

# Verifica estrutura da aba de likes
if not set(["quem_curtiu", "quem_foi_curtido"]).issubset(likes.columns):
    st.error("A aba 'likes' precisa das colunas 'quem_curtiu' e 'quem_foi_curtido'.")
    st.stop()

# Filtra perfis ainda não curtidos
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

# Exibição de dados
st.subheader(perfil.get("nome_publico", "Nome não informado"))
st.text(perfil.get("descricao", ""))
st.markdown("🎵 **Músicas do set:**")
st.text(perfil.get("musicas", ""))

# Exibe fotos
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

# Botões
col1, col2 = st.columns(2)
with col1:
    if st.button("💖 Curtir"):
        # Verifica novamente antes de registrar
        likes_atualizados = likes_ws.get_all_records()
        df_likes = pd.DataFrame(likes_atualizados)
        df_likes.columns = df_likes.columns.str.strip()

        ja_curtiu_este = not df_likes[
            (df_likes["quem_curtiu"] == usuario) & 
            (df_likes["quem_foi_curtido"] == perfil["login"])
        ].empty

        if ja_curtiu_este:
            st.warning("Você já curtiu esse perfil.")
        else:
            likes_ws.append_row([usuario, perfil["login"]])
            st.toast("Like registrado 💘", icon="💘")
            time.sleep(1.2)
            del st.session_state.perfil_atual
            st.rerun()

with col2:
    if st.button("⏩ Pular"):
        del st.session_state.perfil_atual
        st.rerun()
