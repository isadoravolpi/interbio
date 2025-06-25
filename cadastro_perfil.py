import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import tempfile

# --- Escopo de acesso para Google Sheets e Drive ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# --- Autenticação via st.secrets (Streamlit Cloud) ---
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

# Autentica PyDrive
gauth = GoogleAuth()
gauth.credentials = creds.get_access_token().access_token
drive = GoogleDrive(gauth)

# ID da pasta no Google Drive onde as fotos serão salvas
PASTA_DRIVE_ID = "1HXgLg-DiC_kjjQ7UFqzwFLeeR_cqgdA3"  # coloque seu ID aqui

# --- Nome da planilha exata ---
PLANILHA = "TINDER_CEO_PERFIS"

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

st.image("logo_besouro.png", width=400)
st.title("TINDER DA CEÓ 💖")

login = st.text_input("Login privado (será usado depois)")
nome_publico = st.text_input("Nome/apelido")
contato = st.text_input("Instagram, e-mail...")
descricao = st.text_area("3 palavras (ou mais) sobre você")
musicas = st.text_area("Músicas que tocariam no seu set")
fotos = st.file_uploader("Envie até 3 fotos cada uma com no máximo 5 MB", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if fotos and len(fotos) > 3:
    st.warning("Você pode enviar no máximo 3 fotos.")
    st.stop()

if st.button("Enviar"):
    if not all([login, nome_publico, contato, descricao, musicas]) or not fotos:
        st.warning("Preencha todos os campos e envie pelo menos uma foto.")
        st.stop()

    # Valida tamanho de cada arquivo (máximo 5MB)
    for f in fotos:
        tamanho_mb = f.size / (1024 * 1024)
        if tamanho_mb > 5:
            st.warning(f"A foto {f.name} é muito grande ({tamanho_mb:.2f} MB). O máximo permitido é 5 MB.")
            st.stop()

    nomes_fotos = [f"{login}_{i+1}.jpg" for i in range(len(fotos))]

    existentes = aba.col_values(1)
    if login in existentes:
        st.error("Esse login já foi usado. Tente outro.")
        st.stop()

    # Upload das fotos para Google Drive e geração de links
    links_fotos = []
    for f, nome_arquivo in zip(fotos, nomes_fotos):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(f.read())
            tmp.flush()
            arquivo_drive = drive.CreateFile({'title': nome_arquivo, 'parents': [{'id': PASTA_DRIVE_ID}]})
            arquivo_drive.SetContentFile(tmp.name)
            arquivo_drive.Upload()
            link = f"https://drive.google.com/uc?export=view&id={arquivo_drive['id']}"
            links_fotos.append(link)

    # Salva na planilha separando os links por vírgula
    nova_linha = [
        login,
        nome_publico,
        contato,
        descricao,
        musicas,
        ",".join(links_fotos)
    ]
    aba.append_row(nova_linha)

    st.success("Cadastro enviado com sucesso! ✅")



