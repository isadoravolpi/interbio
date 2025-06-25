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
sheet = client.open(PLANILHA)

# Abas obrigatórias
perfis_ws = sheet.worksheet("perfis")

# Tenta acessar ou criar a aba 'likes'
try:
    likes_ws = sheet.worksheet("likes")
except gspread.exceptions.WorksheetNotFound:
    likes_ws = sheet.add_worksheet(title="likes", rows="1000", cols="5")
    likes_ws.append_row(["quem_curtiu", "quem_foi_curtido"])

# Interface principal
st.title("💘LIKES DA CEÓ")

usuario = st.text_input("Digite seu login privado")
if not usuario:
    st.stop()

# Carrega perfis
perfis_data = perfis_ws.get_all_records()
if not perfis_data:
    st.warning("Nenhum perfil cadastrado ainda.")
    st.stop()

df = pd.DataFrame(perfis_data)
df.columns = df.columns.str.strip()

if "login" not in df.columns:
    st.error("A aba 'perfis' precisa da coluna 'login'.")
    st.stop()

# Remove o próprio usuário da lista
df = df[df["login"] != usuario]

# Carrega likes
likes_data = likes_ws.get_all_records()
if not likes_data:
    likes = pd.DataFrame(columns=["quem_curtiu", "quem_foi_curtido"])
else:
    likes = pd.DataFrame(likes_data)
    likes.columns = likes.columns.str.strip()

# Garante que colunas obrigatórias existem
if not set(["quem_curtiu", "quem_foi_curtido"]).issubset(likes.columns):
    st.error("A aba 'likes' precisa das colunas 'quem_curtiu' e 'quem_foi_curtido'.")
    st.stop()

# Filtra perfis não curtidos ainda
ja_curtiu = likes[likes["quem_curtiu"] == usuario]["quem_foi_curtido"].tolist()
df_restantes = df[~df["login"].isin(ja_curtiu)]

if df_restantes.empty:
    st.success("Você já viu todos os perfis disponíveis! Agora é só esperar os matches 🥰")
    st.stop()

# Escolhe um perfil aleatório
perfil = df_restantes.sample(1).iloc[0]

st.subheader(perfil.get("nome_publico", "Nome não informado"))
st.text(perfil.get("descricao", ""))
st.markdown("🎵 **Músicas favoritas:**")
st.text(perfil.get("musicas", ""))

# Mostra nomes das fotos (caso queira exibir futuramente)
st.info("Fotos enviadas:")
st.write(perfil.get("fotos", "Sem fotos"))

col1, col2 = st.columns(2)
with col1:
    if st.button("💖 Curtir"):
    likes_ws.append_row([usuario, perfil["login"]])
    st.rerun()

with col2:
    if st.button("⏩ Pular"):
         st.rerun()
