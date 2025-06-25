import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Escopo de acesso para Google Sheets e Drive ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# --- Autenticação via st.secrets (Streamlit Cloud) ---
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

# --- Nome da planilha exata ---
PLANILHA = "TINDER_CEO_PERFIS"

try:
    sheet = client.open(PLANILHA)
except Exception as e:
    st.error(f"Erro ao abrir a planilha: {e}")
    st.stop()

# Tenta abrir aba "perfis" ou cria se não existir
try:
    aba = sheet.worksheet("perfis")
except gspread.exceptions.WorksheetNotFound:
    aba = sheet.add_worksheet(title="perfis", rows="1000", cols="10")
    aba.append_row(["login", "nome_publico", "contato", "descricao", "musicas", "fotos"])

st.image("logo_besouro.png", width=400)
st.title("TINDER DA CEÓ 💖")

login = st.text_input("Login privado (sera usado depois)")
nome_publico = st.text_input("Nome/apelido")
contato = st.text_input("Instagram, e-mail...")
descricao = st.text_area("3 palavras (ou mais) sobre você")
musicas = st.text_area("Músicas que tocariam no seu set")
fotos = st.file_uploader("Envie até 5 fotos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if st.button("Enviar"):
    if not all([login, nome_publico, contato, descricao, musicas]) or not fotos:
        st.warning("Preencha todos os campos e envie pelo menos uma foto.")
        st.stop()

    nomes_fotos = [f"{login}_{i+1}.jpg" for i in range(len(fotos))]

    # Verifica se login já existe
    existentes = aba.col_values(1)
    if login in existentes:
        st.error("Esse login já foi usado. Tente outro.")
        st.stop()

    # Adiciona nova linha na planilha
    nova_linha = [login, nome_publico, contato, descricao, musicas, ";".join(nomes_fotos)]
    aba.append_row(nova_linha)

    st.success("Cadastro enviado com sucesso para a planilha Google! ✅")

