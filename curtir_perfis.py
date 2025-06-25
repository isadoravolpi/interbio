import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# Autenticação com Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

# Acessa a planilha principal
PLANILHA = "TINDER_CEO_PERFIS"
sheet = client.open(PLANILHA)

# Abas
perfis_ws = sheet.worksheet("perfis")
try:
    likes_ws = sheet.worksheet("likes")
except gspread.exceptions.WorksheetNotFound:
    likes_ws = sheet.add_worksheet(title="likes", rows="1000", cols="5")
    likes_ws.append_row(["quem_curtiu", "quem_foi_curtido"])

# Interface
st.title("💘LIKES DA CEÓ")

usuario = st.text_input("Digite seu login privado")
if not usuario:
    st.stop()

# Carrega perfis com default_blank para evitar conversão de tipos
perfis_data = perfis_ws.get_all_records(default_blank="")
if not perfis_data:
    st.warning("Nenhum perfil cadastrado ainda.")
    st.stop()

df = pd.DataFrame(perfis_data)
df.columns = df.columns.str.strip()

if "login" not in df.columns:
    st.error("A aba 'perfis' precisa da coluna 'login'.")
    st.stop()

df = df[df["login"] != usuario]  # remove o próprio perfil

# Carrega likes
likes_data = likes_ws.get_all_records()
if not likes_data:
    likes = pd.DataFrame(columns=["quem_curtiu", "quem_foi_curtido"])
else:
    likes = pd.DataFrame(likes_data)
    likes.columns = likes.columns.str.strip()

# Proteção contra falta de colunas
if not set(["quem_curtiu", "quem_foi_curtido"]).issubset(likes.columns):
    st.error("A aba 'likes' precisa das colunas 'quem_curtiu' e 'quem_foi_curtido'.")
    st.stop()

# Remove perfis já curtidos
ja_curtiu = likes[likes["quem_curtiu"] == usuario]["quem_foi_curtido"].tolist()
df_restantes = df[~df["login"].isin(ja_curtiu)]

if df_restantes.empty:
    st.success("Você já viu todos os perfis disponíveis! Agora é só esperar os matches 🥰")
    st.stop()

# Seleciona um perfil aleatório
perfil = df_restantes.sample(1).iloc[0]

st.subheader(perfil.get("nome_publico", "Nome não informado"))
st.text(perfil.get("descricao", ""))
st.markdown("🎵 **Músicas do set:**")
st.text(perfil.get("musicas", ""))

# Debug detalhado das fotos
fotos = perfil.get("fotos", "")
st.write("Conteúdo bruto do campo 'fotos':", repr(fotos))

if isinstance(fotos, str) and fotos.strip():
    lista_links = [link.strip() for link in fotos.split(";") if link.strip()]
    st.write("Links após split:", lista_links)

    st.info("Fotos enviadas:")
    cols = st.columns(3)
    for i, link in enumerate(lista_links):
        with cols[i % 3]:
            st.write(f"Link {i}: {link} (tipo: {type(link)})")
            if isinstance(link, str) and link.startswith("http"):
                st.image(link, use_container_width=True)
            else:
                st.write("Link inválido para imagem")
else:
    st.write("Sem fotos para mostrar.")

# Botões de ação
col1, col2 = st.columns(2)
with col1:
    if st.button("💖 Curtir"):
        likes_ws.append_row([usuario, perfil["login"]])
        st.rerun()

with col2:
    if st.button("⏩ Pular"):
        st.rerun()
