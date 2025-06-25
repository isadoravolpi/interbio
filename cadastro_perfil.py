import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# --- Escopo de acesso ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# --- Autenticação com Service Account ---
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

# Autenticação PyDrive usando a mesma credencial
gauth = GoogleAuth()
gauth.credentials = creds
drive = GoogleDrive(gauth)

# --- Configurações ---
PLANILHA = "TINDER_CEO_PERFIS"
PASTA_ID = "1HXgLg-DiC_kjjQ7UFqzwFLeeR_cqgdA3"  # ID da pasta no Google Drive

# Abre planilha e aba
try:
    sheet = client.open(PLANILHA)
except Exception as e:
    st.error(f"Erro ao abrir a planilha: {e}")
    st.stop()

try:
    aba = sheet.worksheet("perfis")
except gspread.exceptions.WorksheetNotFound:
    aba = sheet.add_worksheet(title="perfis", rows="1000", cols="10")
    aba.append_row(["login", "nome_publico", "contato", "descricao", "musicas", "fotos"])

# Interface Streamlit
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

    existentes = aba.col_values(1)
    if login in existentes:
        st.error("Esse login já foi usado. Tente outro.")
        st.stop()

    links_fotos = []
    for i, foto in enumerate(fotos):
        nome_arquivo = f"{login}_{i+1}.jpg"
        # Cria arquivo no Drive na pasta especificada
        file_drive = drive.CreateFile({"title": nome_arquivo, "parents": [{"id": PASTA_ID}]})
        file_drive.SetContentString(foto.getvalue().decode("latin1"))  # Corrigido para conteúdo binário:
        file_drive.content = foto.getbuffer()
        file_drive.Upload()

        # Define permissão pública
        file_drive.InsertPermission({
            'type': 'anyone',
            'value': 'anyone',
            'role': 'reader'
        })

        link = f"https://drive.google.com/uc?id={file_drive['id']}"
        links_fotos.append(link)

    # Salva os links na planilha separados por ;
    nova_linha = [login, nome_publico, contato, descricao, musicas, ";".join(links_fotos)]
    aba.append_row(nova_linha)

    st.success("Cadastro enviado com sucesso! ✅")
