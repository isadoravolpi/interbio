import streamlit as st
import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials

st.title("🧼 Reiniciar o TINDER DA CEÓ")

st.warning("CUIDADO! Essa ação irá apagar todos os dados coletados nas planilhas de perfis, curtidas e matches. As fotos no Drive não serão apagadas.")

if st.button("🔥 Apagar tudo e recomeçar do zero"):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
    client = gspread.authorize(creds)

    PLANILHA = "TINDER_CEO_PERFIS"

    # Tenta abrir a planilha até 3 vezes
    for tentativa in range(3):
        try:
            sheet = client.open(PLANILHA)
            break
        except gspread.exceptions.APIError:
            if tentativa == 2:
                st.error("Erro ao conectar com o Google Sheets. Tente novamente em instantes.")
                st.stop()
            time.sleep(1.5)

    abas = ["perfis", "likes", "matches"]

    for aba_nome in abas:
        try:
            aba = sheet.worksheet(aba_nome)
            all_values = aba.get_all_values()
            if not all_values:
                st.info(f"A aba '{aba_nome}' já está vazia.")
                continue
            cabecalho = all_values[0]
            n_linhas = len(all_values)
            if n_linhas > 1:
                aba.delete_rows(2, n_linhas)
            st.success(f"Aba '{aba_nome}' limpa com sucesso.")
        except gspread.exceptions.WorksheetNotFound:
            st.warning(f"A aba '{aba_nome}' não existe na planilha.")

    st.success("Reset completo! Agora a planilha está limpa, exceto os cabeçalhos.")
else:
    st.info("Nada foi apagado ainda. Clique no botão acima para executar a limpeza.")
