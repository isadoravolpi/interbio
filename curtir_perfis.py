import streamlit as st
import gspread
import pandas as pd
import time
from oauth2client.service_account import ServiceAccountCredentials

# --- Autenticação com Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

PLANILHA = "TINDER_CEO_PERFIS"

# --- Conexão com retry ---
for tentativa in range(3):
    try:
        sheet = client.open(PLANILHA)
        break
    except gspread.exceptions.APIError:
        if tentativa == 2:
            st.error("Erro ao conectar com o Google Sheets. Tente novamente em instantes.")
            st.stop()
        time.sleep(1.5)

# --- Abas ---
perfis_ws = sheet.worksheet("perfis")
try:
    likes_ws = sheet.worksheet("likes")
except gspread.exceptions.WorksheetNotFound:
    likes_ws = sheet.add_worksheet(title="likes", rows="1000", cols="5")
    likes_ws.append_row(["quem_curtiu", "quem_foi_curtido"])

# --- Função para links do Drive ---
def drive_link_para_visualizacao(link):
    if "id=" in link:
        file_id = link.split("id=")[-1]
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return link

# --- Interface ---
st.title("💘LIKES DA CEÓ")

usuario = st.text_input("Digite seu login privado")
if not usuario:
    st.stop()

# --- Cache da planilha ---
@st.cache_data(ttl=30)
def carregar_dados():
    valores = perfis_ws.get_all_values()
    cabecalho, dados = valores[0], valores[1:]
    df = pd.DataFrame(dados, columns=cabecalho)
    df = df.replace("", pd.NA).dropna(how="all")
    df.columns = df.columns.str.strip()
    return df

df = carregar_dados()

if "login" not in df.columns:
    st.error("A aba 'perfis' precisa da coluna 'login'.")
    st.stop()

# --- Remove perfil atual ---
df = df[df["login"] != usuario]

# --- Carrega likes ---
likes_data = likes_ws.get_all_records()
likes = pd.DataFrame(likes_data if likes_data else [], columns=["quem_curtiu", "quem_foi_curtido"])

# --- Remove já curtidos ---
ja_curtiu = likes[likes["quem_curtiu"] == usuario]["quem_foi_curtido"].tolist()
df_restantes = df[~df["login"].isin(ja_curtiu)]

# --- Sorteia um novo perfil se não tiver ainda ---
if "perfil_atual" not in st.session_state or st.session_state.perfil_atual is None:
    if df_restantes.empty:
        st.success("Você já viu todos os perfis disponíveis! Agora é só esperar os matches 🥰")
        st.stop()
    perfil = df_restantes.sample(1).iloc[0].to_dict()
    st.session_state.perfil_atual = perfil
else:
    perfil = st.session_state.perfil_atual

# --- Exibe perfil ---
st.subheader(perfil.get("nome_publico", "Nome não informado"))
st.text(perfil.get("descricao", ""))
st.markdown("🎵 **Músicas do set:**")
st.text(perfil.get("musicas", ""))

# --- Exibe fotos ---
fotos = perfil.get("fotos", "")
if isinstance(fotos, str) and fotos.strip():
    lista_links = [link.strip() for link in fotos.split(";") if link.strip()]
    st.info("Fotos enviadas:")
    cols = st.columns(3)
    for i, link in enumerate(lista_links):
        img_url = drive_link_para_visualizacao(link)
        with cols[i % 3]:
            st.markdown(f'<img src="{img_url}" style="width:100%; border-radius: 10px; margin-bottom:10px;">', unsafe_allow_html=True)
else:
    st.write("Sem fotos para mostrar.")

# --- Botões ---
col1, col2 = st.columns(2)
with col1:
    if st.button("💖 Curtir"):
        likes_ws.append_row([usuario, perfil["login"]])
        st.session_state.perfil_atual = None
        st.rerun()

with col2:
    if st.button("⏩ Pular"):
        st.session_state.perfil_atual = None
        st.rerun()
