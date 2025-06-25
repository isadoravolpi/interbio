import streamlit as st
import gspread
import pandas as pd
import random
from oauth2client.service_account import ServiceAccountCredentials

# Autenticação com Google Sheets via st.secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

# Nome da planilha
PLANILHA = "TINDER_CEO_PERFIS"

# Acessa planilha e abas
sheet = client.open(PLANILHA)
perfis_ws = sheet.worksheet("perfis")

# Cria aba 'likes' se não existir
try:
    likes_ws = sheet.worksheet("likes")
except gspread.exceptions.WorksheetNotFound:
    likes_ws = sheet.add_worksheet(title="likes", rows="1000", cols="5")
    likes_ws.append_row(["quem_curtiu", "quem_foi_curtido"])

# Interface
st.title("LIKES DA CEÓ💘")

usuario = st.text_input("Digite seu login privado")
if not usuario:
    st.stop()

# Lê perfis
df = pd.DataFrame(perfis_ws.get_all_records())
df = df[df["login"] != usuario]

# Lê likes existentes
likes = pd.DataFrame(likes_ws.get_all_records())

if "quem_curtiu" not in likes.columns or "quem_foi_curtido" not in likes.columns:
    st.warning("A aba 'likes' está mal formatada. Verifique o cabeçalho.")
    st.stop()

# Filtra perfis ainda não curtidos
df_restantes = df[~df["login"].isin(ja_curtiu)]

if df_restantes.empty:
    st.success("Você já viu todos os perfis! Agora é só esperar os matches 💘")
    st.stop()

# Embaralha e pega um perfil
perfil = df_restantes.sample(1).iloc[0]

st.subheader(perfil["nome_publico"])
st.text(perfil["descricao"])
st.text("🎵 Músicas favoritas:")
st.text(perfil["musicas"])

# Mostra fotos (somente nomes por enquanto)
st.info("As fotos não estão salvas, mas esses seriam os arquivos:")
st.write(perfil["fotos"])

col1, col2 = st.columns(2)
with col1:
    if st.button("💖 Curtir"):
        likes_ws.append_row([usuario, perfil["login"]])
        st.experimental_rerun()
with col2:
    if st.button("⏩ Pular"):
        st.experimental_rerun()

