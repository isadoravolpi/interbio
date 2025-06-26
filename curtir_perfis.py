import streamlit as st
import gspread
import pandas as pd
import time
import random
from google.oauth2.service_account import Credentials

# 💾 Configurações de autenticação
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)
client = gspread.authorize(creds)

PLANILHA = "TINDER_CEO_PERFIS"

@st.cache_data(ttl=60)
def carregar_sheet():
    for tentativa in range(3):
        try:
            return client.open(PLANILHA)
        except gspread.exceptions.APIError:
            if tentativa == 2:
                st.error("Erro ao conectar ao Google Sheets. Tente novamente.")
                st.stop()
            time.sleep(1.5)

sheet = carregar_sheet()

try:
    perfis_ws = sheet.worksheet("perfis")
    likes_ws = sheet.worksheet("likes")
except gspread.exceptions.WorksheetNotFound:
    st.error("A aba 'perfis' ou 'likes' não foi encontrada na planilha.")
    st.stop()

def drive_link_para_visualizacao(link: str) -> str:
    if "id=" in link:
        file_id = link.split("id=")[-1]
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    if "export=view&id=" in link:
        file_id = link.split("id=")[-1]
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return link

st.title("💘 LIKES DA CEÓ")

usuario = st.text_input("Digite seu login privado")
if not usuario:
    st.stop()

valores = perfis_ws.get_all_values()
if len(valores) < 2:
    st.warning("Nenhum perfil cadastrado ainda.")
    st.stop()

df = pd.DataFrame(valores[1:], columns=[c.strip() for c in valores[0]])
df = df.replace("", pd.NA).dropna(how="all")

if "login" not in df.columns:
    st.error("A aba 'perfis' precisa da coluna 'login'.")
    st.stop()

df = df[df["login"] != usuario]

likes_data = likes_ws.get_all_records()
likes = pd.DataFrame(likes_data) if likes_data else pd.DataFrame(columns=["quem_curtiu", "quem_foi_curtido"])
likes.columns = likes.columns.str.strip()

if not {"quem_curtiu", "quem_foi_curtido"}.issubset(likes.columns):
    st.error("A aba 'likes' precisa das colunas 'quem_curtiu' e 'quem_foi_curtido'.")
    st.stop()

ja_curtiu = likes.loc[likes["quem_curtiu"] == usuario, "quem_foi_curtido"].tolist()
df_restantes = df[~df["login"].isin(ja_curtiu)]

if "perfil_atual" not in st.session_state:
    if df_restantes.empty:
        st.success("Você já viu todos os perfis disponíveis! 🥰")
        st.stop()
    possiveis = df_restantes.to_dict("records")
    random.shuffle(possiveis)
    st.session_state.perfil_atual = possiveis[0]

perfil = st.session_state.perfil_atual

st.subheader(perfil.get("nome_publico", "Nome não informado"))
st.text(perfil.get("descricao", ""))
st.markdown("🎵 **Músicas do set:**")
st.text(perfil.get("musicas", ""))

fotos = perfil.get("fotos", "")
if isinstance(fotos, str) and fotos.strip():
    lista_links = [l.strip() for l in fotos.split(",") if l.strip()]
    st.info("Fotos enviadas:")
    cols = st.columns(3)
    for i, link in enumerate(lista_links):
        img_url = drive_link_para_visualizacao(link)
        with cols[i % 3]:
            st.markdown(
                f'<img src="{img_url}" style="width:100%; border-radius:10px; margin-bottom:10px;">',
                unsafe_allow_html=True
            )
else:
    st.write("Sem fotos para mostrar.")

col1, col2 = st.columns(2)
with col1:
    if st.button("💖 Curtir"):
        df_likes = pd.DataFrame(likes_ws.get_all_records())
        df_likes.columns = df_likes.columns.str.strip()
        ja = not df_likes[
            (df_likes["quem_curtiu"] == usuario) &
            (df_likes["quem_foi_curtido"] == perfil["login"])
        ].empty
        if ja:
            st.warning("Você já curtiu esse perfil.")
        else:
            likes_ws.append_row([usuario, perfil["login"]])
            st.success("Curtida registrada com sucesso 💘")
        del st.session_state.perfil_atual
        st.experimental_rerun()

with col2:
    if st.button("⏩ Pular"):
        del st.session_state.perfil_atual
        st.experimental_rerun()
