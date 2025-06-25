import streamlit as st
import gspread
import pandas as pd
import time
from oauth2client.service_account import ServiceAccountCredentials

# --- Função para conectar com Google Sheets com cache para leitura ---
@st.cache_resource(ttl=600)  # cache 10 minutos, pode ajustar
def conectar_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
    client = gspread.authorize(creds)
    return client

# --- Função para conectar sem cache para escrita ---
def conectar_google_sheets_sem_cache():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
    client = gspread.authorize(creds)
    return client

# --- Função para carregar dados da planilha ---
@st.cache_data(ttl=300)  # cache 5 minutos para dados, para economizar requisições
def carregar_dados(client):
    PLANILHA = "TINDER_CEO_PERFIS"
    sheet = client.open(PLANILHA)
    perfis_ws = sheet.worksheet("perfis")
    likes_ws = sheet.worksheet("likes")

    perfis = pd.DataFrame(perfis_ws.get_all_records())
    likes_raw = pd.DataFrame(likes_ws.get_all_records())

    return perfis, likes_raw, perfis_ws, likes_ws

# --- Início do app ---
st.image("logo_besouro.png", width=400)
st.title("💖 Curtir Perfis - TINDER DA CEÓ")

usuario = st.text_input("Digite seu login privado")
if not usuario:
    st.stop()

client = conectar_google_sheets()
perfis, likes_raw, perfis_ws, likes_ws = carregar_dados(client)

# Remove o próprio usuário dos perfis
perfis = perfis[perfis["login"] != usuario]

# Lista de perfis já curtidos
ja_curtiu = likes_raw[(likes_raw["quem_curtiu"] == usuario)]["quem_foi_curtido"].tolist()

# Perfis restantes para mostrar
df_restantes = perfis[~perfis["login"].isin(ja_curtiu)]

if df_restantes.empty:
    st.success("Você já viu e curtiu todos os perfis disponíveis! 🥰")
    st.stop()

# Perfil atual (usando session_state para manter entre recarregamentos)
if "perfil_atual" not in st.session_state or st.session_state.perfil_atual is None:
    st.session_state.perfil_atual = df_restantes.sample(1).iloc[0].to_dict()

perfil = st.session_state.perfil_atual

# Exibe info do perfil
st.subheader(perfil.get("nome_publico", "Nome não informado"))
st.text(perfil.get("descricao", ""))
st.markdown("🎵 **Músicas do set:**")
st.text(perfil.get("musicas", ""))

# Exibe fotos (assumindo que fotos vêm como links separados por vírgula ou ;)
fotos = perfil.get("fotos", "")
if isinstance(fotos, str) and fotos.strip():
    lista_links = [link.strip() for link in fotos.replace(";", ",").split(",") if link.strip()]
    cols = st.columns(3)
    for i, link in enumerate(lista_links):
        with cols[i % 3]:
            st.image(link, use_container_width=True)
else:
    st.write("Sem fotos para mostrar.")

# Botões de ação
col1, col2 = st.columns(2)
with col1:
    if st.button("💖 Curtir"):
        # Reconectar para escrita sem cache
        client_escrita = conectar_google_sheets_sem_cache()
        sheet_escrita = client_escrita.open("TINDER_CEO_PERFIS")
        likes_ws_escrita = sheet_escrita.worksheet("likes")

        # Recarregar likes para garantir atualizados
        likes_atuais = likes_ws_escrita.get_all_records()

        # Evitar duplicação de like
        ja_curtiu_hoje = any(
            like["quem_curtiu"] == usuario and like["quem_foi_curtido"] == perfil["login"]
            for like in likes_atuais
        )
        if not ja_curtiu_hoje:
            likes_ws_escrita.append_row([usuario, perfil["login"]])
            st.success(f"Você curtiu {perfil.get('nome_publico', perfil['login'])}!")
            time.sleep(1)  # Pausa para evitar quota error
        else:
            st.info("Você já curtiu esse perfil.")

        # Limpa perfil atual para carregar outro
        st.session_state.perfil_atual = None
        st.experimental_rerun()

with col2:
    if st.button("⏩ Pular"):
        st.session_state.perfil_atual = None
        st.experimental_rerun()
