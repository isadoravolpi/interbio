import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# Conexão com Google Sheets (cacheada como recurso para evitar reconexão a todo momento)
@st.cache_resource(ttl=600)
def conectar_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
    client = gspread.authorize(creds)
    return client

# Carrega dados da planilha (cacheada para evitar leituras repetidas)
@st.cache_data(ttl=300)
def carregar_dados():
    client = conectar_google_sheets()
    PLANILHA = "TINDER_CEO_PERFIS"
    sheet = client.open(PLANILHA)
    perfis_ws = sheet.worksheet("perfis")
    likes_ws = sheet.worksheet("likes")

    perfis = pd.DataFrame(perfis_ws.get_all_records())
    likes_raw = pd.DataFrame(likes_ws.get_all_records())
    return perfis, likes_raw, perfis_ws, likes_ws

# Exemplo simples de uso dentro do Streamlit
def main():
    st.title("💖 Curtir Perfis")

    # Carregar os dados
    perfis, likes_raw, perfis_ws, likes_ws = carregar_dados()

    # Suponha que o usuário logado seja este
    usuario = st.text_input("Digite seu login privado")
    if not usuario:
        st.stop()

    # Filtra perfis que o usuário já curtiu para evitar repetição
    curtidos = likes_raw[likes_raw["quem_curtiu"] == usuario]["quem_foi_curtido"].unique().tolist()

    # Perfis que o usuário ainda não curtiu
    perfis_disp = perfis[~perfis["login"].isin(curtidos) & (perfis["login"] != usuario)]

    if perfis_disp.empty:
        st.info("Não há mais perfis para curtir 😢")
        st.stop()

    # Mostra o primeiro perfil disponível
    perfil = perfis_disp.iloc[0]

    st.subheader(f"{perfil['nome_publico']}")

    # Mostra descrição, músicas, fotos, etc
    st.text(f"Contato: {perfil['contato']}")
    st.text(f"Descrição: {perfil['descricao']}")
    st.text(f"Músicas: {perfil['musicas']}")

    # Fotos: separado por vírgula, mostra todas
    fotos = perfil["fotos"].split(",")
    for foto_url in fotos:
        st.image(foto_url.strip())

    if st.button("Curtir"):
        # Adiciona curtida na planilha de likes
        likes_ws.append_row([usuario, perfil["login"]])
        st.success(f"Você curtiu {perfil['nome_publico']}!")
        st.experimental_rerun()

if __name__ == "__main__":
    main()
