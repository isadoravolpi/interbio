import streamlit as st
import pandas as pd
import os

st.title("💍 Veja seus Matches - TINDER DA CEÓ")

usuario = st.text_input("Digite seu nome de login privado (igual cadastrado)")
if not usuario:
    st.stop()

if not os.path.exists("matches_completos.csv"):
    st.error("O arquivo de matches ainda não foi gerado.")
    st.stop()

df = pd.read_csv("matches_completos.csv")
meus_matches = df[df["eu"] == usuario]

if meus_matches.empty:
    st.info("Ainda não rolou nenhum match 😢 Mas vai acontecer!")
    st.stop()

st.success(f"Você teve {len(meus_matches)} match(es)! 🎉")
for _, row in meus_matches.iterrows():
    st.subheader(f"{row['match_nome_publico']} 💖")
    st.text(f"Contato: {row['contato']}")
    st.text(f"Descrição: {row['descricao']}")
    st.text("Músicas favoritas:")
    st.text(row["musicas"])

    fotos = row["fotos"].strip("[]").replace("'", "").split(", ")
    for foto_nome in fotos:
        caminho_foto = os.path.join("uploads", row["match_login"], foto_nome)
        if os.path.exists(caminho_foto):
            st.image(caminho_foto, use_column_width=True)

    st.markdown("---")