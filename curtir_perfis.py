import streamlit as st
import gspread
import pandas as pd
import time
from oauth2client.service_account import ServiceAccountCredentials

# --- Autenticação Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

PLANILHA = "TINDER_CEO_PERFIS"

# Função para abrir planilha com retry
def abrir_planilha_com_retry(nome, tentativas=3, delay=1.5):
    for tentativa in range(tentativas):
        try:
            return client.open(nome)
        except gspread.exceptions.APIError as e:
            if tentativa == tentativas - 1:
                st.error("Erro ao conectar com o Google Sheets. Tente novamente em instantes.")
                st.stop()
            time.sleep(delay)

sheet = abrir_planilha_com_retry(PLANILHA)

# Acessa as abas
perfis_ws = sheet.worksheet("perfis")
try:
    likes_ws = sheet.worksheet("likes")
except gspread.exceptions.WorksheetNotFound:
    likes_ws = sheet.add_worksheet(title="likes", rows="1000", cols="5")
    likes_ws.append_row(["quem_curtiu", "quem_foi_curtido"])

# Cache para carregar perfis
@st.cache_data(ttl=60)
def carregar_perfis():
    valores = perfis_ws.get_all_values()
    if not valores:
        return pd.DataFrame()
    cabecalho, dados = valores[0], valores[1:]
    df = pd.DataFrame(dados, columns=cabecalho)
    df = df.replace("", pd.NA).dropna(how="all")
    df.columns = df.columns.str.strip()
    return df

# Cache para carregar likes
@st.cache_data(ttl=30)
def carregar_likes():
    likes_data = likes_ws.get_all_records()
    if not likes_data:
        return pd.DataFrame(columns=["quem_curtiu", "quem_foi_curtido"])
    df_likes = pd.DataFrame(likes_data)
    df_likes.columns = df_likes.columns.str.strip()
    return df_likes

# Função para converter link do Google Drive para URL de visualização direta
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

df = carregar_perfis()
if df.empty:
    st.warning("Nenhum perfil cadastrado ainda.")
    st.stop()

if "login" not in df.columns:
    st.error("A aba 'perfis' precisa da coluna 'login'.")
    st.stop()

df = df[df["login"] != usuario]

likes = carregar_likes()
if not set(["quem_curtiu", "quem_foi_curtido"]).issubset(likes.columns):
    st.error("A aba 'likes' precisa das colunas 'quem_curtiu' e 'quem_foi_curtido'.")
    st.stop()

ja_curtiu = likes[likes["quem_curtiu"] == usuario]["quem_foi_curtido"].tolist()

if "ultimo_login" not in st.session_state:
    st.session_state.ultimo_login = None

# Perfis restantes que não foram curtidos e não foram o último exibido
df_restantes = df[~df["login"].isin(ja_curtiu)]
if st.session_state.ultimo_login:
    df_restantes = df_restantes[df_restantes["login"] != st.session_state.ultimo_login]

if df_restantes.empty:
    st.success("Você já viu todos os perfis disponíveis! Agora é só esperar os matches 🥰")
    st.stop()

# Escolhe perfil para mostrar se não estiver salvo
if "perfil_atual" not in st.session_state or st.session_state.perfil_atual is None:
    perfil = df_restantes.sample(1).iloc[0]
    st.session_state.perfil_atual = perfil.to_dict()
else:
    perfil = pd.Series(st.session_state.perfil_atual)

# Exibe dados do perfil
st.subheader(perfil.get("nome_publico", "Nome não informado"))
st.text(perfil.get("descricao", ""))
st.markdown("🎵 **Músicas do set:**")
st.text(perfil.get("musicas", ""))

# Exibe fotos em grid 3 colunas
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

# Botões Curtir e Pular com keys para evitar conflito
col1, col2 = st.columns(2)
with col1:
    if st.button("💖 Curtir", key="curtir"):
        likes_ws.append_row([usuario, st.session_state.perfil_atual["login"]])
        st.cache_data.clear()
        st.session_state.ultimo_login = st.session_state.perfil_atual["login"]
        st.session_state.perfil_atual = None
        st.rerun()

with col2:
    if st.button("⏩ Pular", key="pular"):
        st.session_state.ultimo_login = st.session_state.perfil_atual["login"]
        st.session_state.perfil_atual = None
        st.rerun()
