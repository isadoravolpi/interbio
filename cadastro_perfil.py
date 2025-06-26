import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import tempfile
import ssl
import socket
import httplib2  # para capturar SSLHandshakeError

# Escopos
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def carregar_credenciais():
    creds_dict = st.secrets["gcp_service_account"]
    return ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)

@st.cache_resource
def conectar_google_sheets():
    creds = carregar_credenciais()
    return gspread.authorize(creds)

@st.cache_resource
def conectar_drive():
    creds = carregar_credenciais()
    return build('drive', 'v3', credentials=creds)

client = conectar_google_sheets()
drive_service = conectar_drive()

PASTA_DRIVE_ID = "1HXgLg-DiC_kjjQ7UFqzwFLeeR_cqgdA3"
PLANILHA = "TINDER_CEO_PERFIS"

@st.cache_resource
def abrir_aba_perfis():
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
    return aba

aba = abrir_aba_perfis()

# ------------------- INTERFACE ----------------------

st.image("logo_besouro.png", width=400)
st.title("TINDER DA CEÓ 💖")

login = st.text_input("Login privado (será usado depois)")
nome_publico = st.text_input("Nome/apelido")
contato = st.text_input("WPP, Instagram...")
descricao = st.text_area("3 palavras (ou mais) sobre você")
musicas = st.text_area("Músicas que tocariam no seu set")
fotos = st.file_uploader(
    "Envie até 3 fotos, cada uma com no máximo 5 MB",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

# Pré-visualização
if fotos:
    st.markdown("### Pré-visualização das fotos:")
    cols = st.columns(3)
    for i, foto in enumerate(fotos):
        with cols[i % 3]:
            st.image(foto, use_container_width=True)

if fotos and len(fotos) > 3:
    st.warning("Você pode enviar no máximo 3 fotos.")
    st.stop()

@st.cache_data(ttl=30)
def carregar_logins():
    return aba.col_values(1)

if st.button("Enviar"):
    if not all([login, nome_publico, contato, descricao, musicas]) or not fotos:
        st.warning("Preencha todos os campos e envie pelo menos uma foto.")
        st.stop()

    for f in fotos:
        tamanho_mb = f.size / (1024 * 1024)
        if tamanho_mb > 5:
            st.warning(f"A foto {f.name} é muito grande ({tamanho_mb:.2f} MB). Máximo permitido: 5 MB.")
            st.stop()

    existentes = carregar_logins()
    if login in existentes:
        st.error("Esse login já foi usado. Tente outro.")
        st.stop()

    nomes_fotos = [f"{login}_{i+1}.jpg" for i in range(len(fotos))]
    links_fotos = []

    try:
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

           # 🔓 Deixa a imagem pública
            file_id = uploaded_file.get('id')
            drive_service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
            fields="id"
            ).execute()

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

    except (ssl.SSLEOFError, ssl.SSLError, socket.error, httplib2.SSLHandshakeError):
        st.error("⚠️ Erro temporário de conexão segura (SSL). Recarregue a página e tente novamente.")
        st.stop()

    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        st.stop()
