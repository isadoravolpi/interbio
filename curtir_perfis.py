import streamlit as st
import gspread
import pandas as pd
import random
import time
from google.oauth2.service_account import Credentials

# Autenticação
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Nome da planilha
PLANILHA = "TINDER_CEO_PERFIS"

# Carrega planilha (sem cache direto no objeto gspread)
def carregar_sheet():
    for tentativa in range(3):
        try:
            return client.open(PLANILHA)
        except Exception as e:
            if hasattr(e, "response") and hasattr(e.response, "status_code"):
                if e.response.status_code == 429:
                    st.warning("⏳ O sistema atingiu o limite de acessos por minuto. Aguarde alguns segundos e recarregue a página.")
                    st.stop()
            if tentativa == 2:
                st.error(f"Erro ao abrir planilha: {e}")
                st.stop()
            time.sleep(1.5)


sheet = carregar_sheet()

# Acessa abas
def garantir_aba(nome, colunas):
    try:
        ws = sheet.worksheet(nome)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=nome, rows="1000", cols=str(len(colunas)))
        ws.append_row(colunas)
    return ws

perfis_ws = garantir_aba("perfis", ["login", "nome_publico", "descricao", "musicas", "fotos"])
likes_ws = garantir_aba("likes", ["quem_curtiu", "quem_foi_curtido"])
passados_ws = garantir_aba("passados", ["quem_passou", "quem_foi_passado"])

# Função de link do drive
def drive_link_para_visualizacao(link):
    import re

    # Extrai o ID do link, qualquer que seja o formato
    match = re.search(r'id=([a-zA-Z0-9_-]+)', link)
    if not match:
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
    if not match:
        return link  # retorna original se não encontrar nada

    file_id = match.group(1)

    # Volta ao formato uc?export=view que funciona em todos dispositivos
    return f"https://drive.google.com/uc?export=view&id={file_id}"


# Funções para carregar dados da planilha (sem cache)
def carregar_perfis(ws):
    return ws.get_all_values()

def carregar_likes(ws):
    return ws.get_all_records()

def carregar_passados(ws):
    return ws.get_all_records()

# Funções para processar dados e aplicar cache
@st.cache_data(ttl=15)
def processar_perfis(valores):
    if not valores:
        return None
    cabecalho, dados = valores[0], valores[1:]
    df = pd.DataFrame(dados, columns=cabecalho).replace("", pd.NA).dropna(how="all")
    df.columns = df.columns.str.strip()
    return df

@st.cache_data(ttl=15)
def processar_likes(likes_data):
    if not likes_data:
        return pd.DataFrame(columns=["quem_curtiu", "quem_foi_curtido"])
    df = pd.DataFrame(likes_data)
    df.columns = df.columns.str.strip()
    return df

@st.cache_data(ttl=15)
def processar_passados(passados_data):
    if not passados_data:
        return pd.DataFrame(columns=["quem_passou", "quem_foi_passado"])
    df = pd.DataFrame(passados_data)
    df.columns = df.columns.str.strip()
    return df

# App principal
st.image("logo_besouro.png", width=400)
st.title("💘 LIKES DA CEÓ")
usuario = st.text_input("Digite seu login privado")
if not usuario:
    st.stop()

# Dados dos perfis (session_state)
if "valores_perfis" not in st.session_state:
    try:
        st.session_state.valores_perfis = carregar_perfis(perfis_ws)
    except Exception as e:
        st.error(f"Erro ao carregar perfis: {e}")
        st.stop()
valores = st.session_state.valores_perfis

df = processar_perfis(valores)
if df is None or df.empty:
    st.warning("Nenhum perfil cadastrado ainda.")
    st.stop()

if "login" not in df.columns:
    st.error("A aba 'perfis' precisa da coluna 'login'.")
    st.stop()

df = df[df["login"] != usuario]

# Dados de likes e passados (session_state)
if "likes_data" not in st.session_state:
    likes_data = carregar_likes(likes_ws)
    st.session_state.likes_data = likes_data
else:
    likes_data = st.session_state.likes_data

likes = processar_likes(likes_data)

if "passados_data" not in st.session_state:
    passados_data = carregar_passados(passados_ws)
    st.session_state.passados_data = passados_data
else:
    passados_data = st.session_state.passados_data

passados = processar_passados(passados_data)

ja_curtiu = likes[likes["quem_curtiu"] == usuario]["quem_foi_curtido"].tolist()
ja_passou = passados[passados["quem_passou"] == usuario]["quem_foi_passado"].tolist()

# Excluir perfis já vistos
df_restantes = df[~df["login"].isin(ja_curtiu + ja_passou)]

if df_restantes.empty:
    st.success("Você já viu todos os perfis disponíveis! Agora é só esperar os matches 🥰")
    st.stop()

# Sorteia perfil atual
if "perfil_atual" not in st.session_state:
    perfis_possiveis = df_restantes.to_dict("records")
    random.shuffle(perfis_possiveis)
    st.session_state.perfil_atual = perfis_possiveis[0]

perfil = st.session_state.perfil_atual

# Exibição do perfil
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

# Botões de ação
col1, col2 = st.columns(2)

with col1:
    if st.button("💖 Curtir"):
        try:
            likes_ws.append_row([usuario, perfil["login"]])
            st.session_state.likes_data.append({"quem_curtiu": usuario, "quem_foi_curtido": perfil["login"]})
            st.success("Curtida registrada com sucesso 💘")
        except Exception as e:
            st.error(f"Erro ao registrar curtida: {e}")
        del st.session_state.perfil_atual
        st.rerun()

with col2:
    if st.button("⏩ Pular"):
        try:
            passados_ws.append_row([usuario, perfil["login"]])
            st.session_state.passados_data.append({"quem_passou": usuario, "quem_foi_passado": perfil["login"]})
        except Exception as e:
            st.error(f"Erro ao registrar pulo: {e}")
        del st.session_state.perfil_atual
        st.rerun()
