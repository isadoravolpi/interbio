import streamlit as st
import os
import pandas as pd

# Caminhos para salvar dados e fotos
PERFIS_CSV = "perfis.csv"
FOTOS_DIR = "fotos"

# Cria diretórios se não existirem
os.makedirs(FOTOS_DIR, exist_ok=True)

# Layout
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.image("logo_besouro.png", width=400)
    st.title("TINDER DA CEÓ 💖")

# Inputs do usuário
login = st.text_input("Crie um nome de login privado (será usado depois para logar)")
nome_publico = st.text_input("Nome/apelido")
contato = st.text_input("Seu contato (e-mail, Instagram, etc.)")
descricao = st.text_area("3 palavras (ou mais) sobre você")
musicas = st.text_area("Músicas que tocariam no seu set")
fotos = st.file_uploader("Envie até 5 fotos", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

# Botão de envio
if st.button("Enviar"):
    if not all([login, nome_publico, contato, descricao, musicas]) or not fotos:
        st.warning("Preencha todos os campos e envie ao menos uma foto.")
        st.stop()

    # Nomeia fotos com base no login
    nomes_fotos = []
    for i, foto in enumerate(fotos):
        nome_arquivo = f"{login}_{i+1}.jpg"
        caminho_foto = os.path.join(FOTOS_DIR, nome_arquivo)
        with open(caminho_foto, "wb") as f:
            f.write(foto.read())
        nomes_fotos.append(nome_arquivo)

    # Carrega o CSV existente ou cria novo
    if os.path.exists(PERFIS_CSV):
        perfis_df = pd.read_csv(PERFIS_CSV)
        if login in perfis_df["login"].values:
            st.error("Esse login já existe! Escolha outro.")
            st.stop()
    else:
        perfis_df = pd.DataFrame(columns=["login", "nome_publico", "contato", "descricao", "musicas", "fotos"])

    # Salva os dados
    novo_perfil = pd.DataFrame([{
        "login": login,
        "nome_publico": nome_publico,
        "contato": contato,
        "descricao": descricao,
        "musicas": musicas,
        "fotos": ";".join(nomes_fotos)
    }])
    perfis_df = pd.concat([perfis_df, novo_perfil], ignore_index=True)
    perfis_df.to_csv(PERFIS_CSV, index=False)

    st.success("Perfil enviado com sucesso! 💕")
