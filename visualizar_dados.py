import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Autenticação com Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

# Nome da planilha
PLANILHA = "TINDER_CEO_PERFIS"

# Interface
st.title("📊 Visualizar Dados do App")

opcao = st.selectbox("O que deseja visualizar?", ["Usuários", "Curtidas", "Matches"])

# Mapeia opção para aba da planilha
aba_mapeada = {
    "Usuários": "perfis",
    "Curtidas": "likes",
    "Matches": "matches"
}

aba_nome = aba_mapeada[opcao]

# Tenta carregar os dados
try:
    ws = client.open(PLANILHA).worksheet(aba_nome)
    valores = ws.get_all_values()
    cabecalho, dados = valores[0], valores[1:]
    df = pd.DataFrame(dados, columns=cabecalho)
except Exception as e:
    st.error(f"Erro ao carregar dados da aba '{aba_nome}': {e}")
    st.stop()

# Exibe e permite baixar
if df.empty:
    st.write(f"Nenhum dado encontrado na aba '{aba_nome}'.")
else:
    st.dataframe(df)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(f"⬇️ Baixar CSV de {opcao}", csv, f"{aba_nome}.csv", "text/csv")
