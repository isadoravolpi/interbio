import streamlit as st
import gspread
import pandas as pd
import random
import time
from google.oauth2.service_account import Credentials

# --- AUTENTICAÇÃO ---
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# --- NOME DA PLANILHA ---
PLANILHA = "TINDER_CEO_PERFIS"

# --- ABRINDO PLANILHA (sem cache) ---
def carregar_sheet():
    for tentativa in range(3):
        try:
            return client.open(PLANILHA)
        except Exception:
            if tentativa == 2:
                st.error("Erro ao conectar ao Google Sheets. Tente novamente.")
                st.stop()
            time.sleep(1.5)

sheet = carregar_sheet()

# --- GARANTINDO EXISTÊNCIA DAS ABAS (sem cache) ---
def garantir_aba(nome, colunas):
    try:
        ws = sheet.worksheet(nome)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=nome, rows="1000", cols=str(len(colunas)))
        ws.append_row(colunas)
    return ws

perfis_ws = garantir_aba("perfis", [])  # colunas não necessárias aqui
likes_ws = garantir_aba("likes", ["quem_curtiu", "quem_foi_curtido"])
passados_ws = garantir_aba("passados", ["quem_passou", "quem_foi_passado"])

# --- FUNÇÕES PARA CARREGAR DADOS DAS ABAS (com cache) ---
@st.cache_data(ttl=15)
def carregar_perfis(ws):
    return ws.get_all_values()

@st.cache_data(ttl=15)
def carregar_likes(ws):
    return ws.get_all_records()

@st.cache_data(ttl=15)
def carregar_passados(ws):
    return ws.get_all_records()

# --- FUNÇÃO PARA FORMATAR LINK DRIVE ---
def drive_link_para_visualizacao(link):
    if "id=" in link:
        file_id = link.split("id=")[-1]
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    elif "export=view&id=" in link:
        file_id = link.split("id=")[-1]
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return link

# --- INÍCIO DO APP ---
st.image("logo_besouro.png", width=400)
st.title("💘 LIKES DA CEÓ")

usuario = st.text_input("Digite seu login privado")
if not usuario:
    st.stop()

# --- CARREGAR DADOS ---
valores = carregar_perfis(perfis_ws)
if not valores:
    st.warning("Nenhum perfil cadastrado ainda.")
    st.stop()

cabecalho, dados = valores[0], valores[1:]
df = pd.DataFrame(dados, columns=cabecalho).replace("", pd.NA).dropna(how="all")
df.columns = df.columns.str.strip()

if "login" not in df.columns:
    st.error("A aba 'perfis' precisa da coluna 'login'.")
    st.stop()

df = df[df["login"] != usuario]

likes_data = carregar_likes(likes_ws)
likes = pd.DataFrame(likes_data) if likes_data else pd.DataFrame(columns=["quem_curtiu", "quem_foi_curtido"])
likes.columns = likes.columns.str.strip()

passados_data = carregar_passados(passados_ws)
passados = pd.DataFrame(passados_data) if passados_data else pd.DataFrame(columns=["quem_passou", "quem_foi_passado"])
passados.columns = passados.columns.str.strip()

ja_curtiu = likes[likes["quem_curtiu"] == usuario]["quem_foi_curtido"].tolist()
ja_passou = passados[passados["quem_passou"] == usuario]["quem_foi_passado"].tolist()

df_restantes = df[~df["login"].isin(ja_curtiu + ja_passou)]

if df_restantes.empty:
    st.success("Você já viu todos os perfis disponíveis! Agora é só esperar os matches 🥰")
    st.stop()

# --- ESCOLHER PERFIL ---
if "perfil_atual" not in st.session_state:
    perfis_possiveis = df_restantes.to_dict("records")
    random.shuffle(perfis_possiveis)
    st.session_state.perfil_atual = perfis_possiveis[0]

perfil = st.session_state.perfil_atual

# --- EXIBIÇÃO DO PERFIL ---
st.subheader(perfil.get("nome_publico", "Nome não informado"))
st.text(perfil.get("descricao", ""))
st.markdown("🎵 **Músicas do set:**")
st.text(perfil.get("musicas", ""))

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

# --- BOTÕES ---
col1, col2 = st.columns(2)

with col1:
    if st.button("💖 Curtir"):
        try:
            likes_ws.append_row([usuario, perfil["login"]])
            st.success("Curtida registrada com sucesso 💘")
        except Exception as e:
            st.error(f"Erro ao registrar curtida: {e}")
        del st.session_state.perfil_atual
        st.rerun()

with col2:
    if st.button("⏩ Pular"):
        try:
            passados_ws.append_row([usuario, perfil["login"]])
        except Exception as e:
            st.error(f"Erro ao registrar pulo: {e}")
        del st.session_state.perfil_atual
        st.rerun()
