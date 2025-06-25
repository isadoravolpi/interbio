import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time

# --- Configurações ---

PLANILHA = "TINDER_CEO_PERFIS"
PAGINA_PERFIS = "perfis"
PAGINA_LIKES = "likes"

# --- Funções de conexão e carregamento ---

@st.cache_resource(ttl=600)
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
    client = gspread.authorize(creds)
    return client

@st.cache_data(ttl=300)
def carregar_dados(planilha_nome):
    client = conectar_google_sheets()
    sheet = client.open(planilha_nome)
    perfis_ws = sheet.worksheet(PAGINA_PERFIS)
    try:
        likes_ws = sheet.worksheet(PAGINA_LIKES)
    except gspread.exceptions.WorksheetNotFound:
        likes_ws = sheet.add_worksheet(title=PAGINA_LIKES, rows="1000", cols="5")
        likes_ws.append_row(["quem_curtiu", "quem_foi_curtido"])

    perfis = perfis_ws.get_all_values()
    likes = likes_ws.get_all_records()
    return perfis, likes, perfis_ws, likes_ws

def drive_link_para_visualizacao(link):
    if "id=" in link:
        file_id = link.split("id=")[-1]
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return link

# --- Início do app ---

st.image("logo_besouro.png", width=400)
st.title("💖 Curtir Perfis - TINDER DA CEÓ")

usuario = st.text_input("Digite seu login privado")
if not usuario:
    st.stop()

perfis, likes_raw, perfis_ws, likes_ws = carregar_dados(PLANILHA)

if not perfis:
    st.warning("Nenhum perfil cadastrado ainda.")
    st.stop()

cabecalho, dados = perfis[0], perfis[1:]
df_perfis = pd.DataFrame(dados, columns=cabecalho)
df_perfis = df_perfis.replace("", pd.NA).dropna(how="all")
df_perfis.columns = df_perfis.columns.str.strip()

if "login" not in df_perfis.columns:
    st.error("A aba 'perfis' precisa conter a coluna 'login'.")
    st.stop()

df_perfis = df_perfis[df_perfis["login"] != usuario]

df_likes = pd.DataFrame(likes_raw) if likes_raw else pd.DataFrame(columns=["quem_curtiu", "quem_foi_curtido"])
df_likes.columns = df_likes.columns.str.strip()

if not set(["quem_curtiu", "quem_foi_curtido"]).issubset(df_likes.columns):
    st.error("A aba 'likes' precisa conter as colunas 'quem_curtiu' e 'quem_foi_curtido'.")
    st.stop()

ja_curtiu = df_likes[df_likes["quem_curtiu"] == usuario]["quem_foi_curtido"].unique().tolist()
df_restantes = df_perfis[~df_perfis["login"].isin(ja_curtiu)]

if "perfil_atual" not in st.session_state:
    if df_restantes.empty:
        st.success("Você já viu todos os perfis disponíveis! Agora é só esperar os matches 🥰")
        st.stop()
    st.session_state.perfil_atual = df_restantes.sample(1).iloc[0].to_dict()

perfil = st.session_state.perfil_atual

# Mostrar dados do perfil
st.subheader(perfil.get("nome_publico", "Nome não informado"))
st.text(perfil.get("descricao", ""))
st.markdown("🎵 **Músicas do set:**")
st.text(perfil.get("musicas", ""))

# Mostrar fotos
fotos = perfil.get("fotos", "")
if isinstance(fotos, str) and fotos.strip():
    lista_links = [link.strip() for link in fotos.split(",") if link.strip()]
    st.info("Fotos enviadas:")
    cols = st.columns(min(3, len(lista_links)))
    for i, link in enumerate(lista_links):
        img_url = drive_link_para_visualizacao(link)
        with cols[i % 3]:
            st.image(img_url, use_container_width=True)
else:
    st.write("Sem fotos para mostrar.")

# Botões de ação
col1, col2 = st.columns(2)

with col1:
    if st.button("💖 Curtir"):
        # Evitar likes duplicados
        if (df_likes[(df_likes["quem_curtiu"] == usuario) & (df_likes["quem_foi_curtido"] == perfil["login"])].empty):
            likes_ws.append_row([usuario, perfil["login"]])
            st.success(f"Você curtiu {perfil.get('nome_publico', perfil['login'])}!")
        else:
            st.info("Você já curtiu esse perfil antes.")

        # Atualiza perfil atual para o próximo
        st.session_state.perfil_atual = None
        st.experimental_rerun()

with col2:
    if st.button("⏩ Pular"):
        st.session_state.perfil_atual = None
        st.experimental_rerun()
