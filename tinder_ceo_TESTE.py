import streamlit as st
import os
import pandas as pd

os.makedirs("uploads", exist_ok=True)

col1, col2, col3 = st.columns([1, 3, 1])
with col2:st.image("logo_besouro.png", width=400)
with col2:st.title("TINDER DA CEÓ 💖")

nome_privado = st.text_input("Crie um nome de login privado (será usado depois)")
nome_publico = st.text_input("Nome/apelido")
contato = st.text_input("Seu contato (e-mail, Instagram, etc.)")
descricao = st.text_area("3 palavras (ou mais) sobre você")
musicas = st.text_area("Músicas que tocariam no seu set")
fotos = st.file_uploader("Envie até 5 fotos", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if st.button("Enviar"):
    if nome_privado and nome_publico and contato and fotos:
        pessoa_dir = f"uploads/{nome_privado}"
        os.makedirs(pessoa_dir, exist_ok=True)

        for i, foto in enumerate(fotos):
            with open(f"{pessoa_dir}/foto_{i+1}.jpg", "wb") as f:
                f.write(foto.read())

        dados = pd.DataFrame([{
            "nome_privado": nome_privado,
            "nome_publico": nome_publico,
            "contato": contato,
            "descricao": descricao,
            "musicas": musicas,
            "fotos": [f"foto_{i+1}.jpg" for i in range(len(fotos))]
        }])

        dados.to_csv(f"{pessoa_dir}/dados.csv", index=False)
        st.success("Dados enviados com sucesso! 🎉")
    else:
        st.warning("Preencha todos os campos e envie ao menos uma foto.")
