import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import tempfile

# Escopos
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Cache das credenciais
@st.cache_resource
def carregar_credenciais():
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
    return creds

# Autenticação
creds = carregar_credenciais()

# Cache do client do Google Sheets
@st.cache_resource
def conectar_google_sheets(creds):
    return gspread.authorize(creds)

client = conectar_google_sheets(creds)

# Cache do serviço do Google Drive
@st.cache_resource
def conectar_drive(creds):
    return build('drive', 'v3', credentials=creds)

drive_service = conectar_drive(creds)

# ID da pasta para fotos no Drive
PASTA_DRIVE_ID = "1HXgLg-DiC_kjjQ7UFqzwFLeeR_cqgdA3"

# Nome da planilha
PLANILHA = "TINDER_CEO_PERFIS"

# Abrir planilha e aba "perfis"
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

# ------------------- INTERFACE ----------------------

st.image("logo_besouro.png", width=400)
st.title("TINDER DA CEÓ 💖")

login = st.text_input("Login privado (será usado depois)")
nome_publico = st.text_input("Nome/apelido")
contato = st.text_input("Instagram, e-mail...")
descricao = st.text_area("3 palavras (ou mais) sobre você")
musicas = st.text_area("Músicas que tocariam no seu set")
fotos = st.file_uploader(
    "Envie até 3 fotos, cada uma com no máximo 5 MB",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if fotos and len(fotos) > 3:
    st.warning("Você pode enviar no máximo 3 fotos.")
    st.stop()

# Função para obter logins existentes com cache
@st.cache_data(ttl=30)
def carregar_logins(aba):
    return aba.col_values(1)

if st.button("Enviar"):
    if not all([login, nome_publico, contato, descricao, musicas]) or not fotos:
        st.warning("Preencha todos os campos e envie pelo menos uma foto.")
        st.stop()

    # Valida tamanho das fotos
    for f in fotos:
        tamanho_mb = f.size / (1024 * 1024)
        if tamanho_mb > 5:
            st.warning(f"A foto {f.name} é muito grande ({tamanho_mb:.2f} MB). Máximo permitido: 5 MB.")
            st.stop()

    nomes_fotos = [f"{login}_{i+1}.jpg" for i in range(len(fotos))]

    existentes = carregar_logins(aba)
    if login in existentes:
        st.error("Esse login já foi usado. Tente outro.")
        st.stop()

    links_fotos = []

    for f, nome_arquivo in zip(fotos, nomes_fotos):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(f.read())
            tmp.flush()

            file_metadata = {
                'name': nome_arquivo,
                'parents': [PASTA_DRIVE_ID]
            }
            media = MediaFileUpload(tmp.name, mimetype='image/jpeg')
            uploaded_file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            file_id = uploaded_file.get('id')
            link = f"https://drive.google.com/uc?export=view&id={file_id}"
            links_fotos.append(link)

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
