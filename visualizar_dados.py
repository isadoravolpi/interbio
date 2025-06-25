import streamlit as st
import pandas as pd
import os

st.title("Visualizar Dados")

opcao = st.selectbox("O que deseja visualizar?", ["Usuários", "Curtidas", "Matches"])

def carregar_arquivo(nome):
    if os.path.exists(nome):
        return pd.read_csv(nome)
    return pd.DataFrame()

df = carregar_arquivo(f"{opcao.lower()}.csv")

if df.empty:
    st.write(f"Nenhum dado encontrado para {opcao}.")
else:
    st.dataframe(df)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(f"Baixar CSV de {opcao}", csv, f"{opcao.lower()}.csv", "text/csv")
