import streamlit as st
import os
import pandas as pd
import random

PERFIS_CSV = "perfis.csv"
LIKES_CSV = "likes.csv"
FOTOS_DIR = "fotos"

# Título e login
st.title("🔥 MATCH - TINDER DA CEÓ")

usuario = st.text_input("Digite seu login privado (exatamente como cadastrou)")
if not usuario:
    st.stop()

# Verifica se o arquivo de perfis existe
if not os.path.exists(PERFIS_CSV):
    st.error("Nenhum perfil encontrado. Cadastre-se primeiro.")
    st.stop()

# Carrega perfis
perfis_df = pd.read_csv(PERFIS_CSV)

# Verifica se o login existe
if usuario not in perfis_df["login"].values:
    st.error("Login não encontrado. Verifique o nome ou cadastre-se.")
    st.stop()

# Carrega likes
if os.path.exists(LIKES_CSV):
    likes_df = pd.read_csv(LIKES_CSV)
else:
    likes_df = pd.DataFrame(columns=["usuario", "curtido"])

ja_curtiu = likes_df.loc[likes_df["usuario"] == usuario, "curtido"].tolist()

# Filtra perfis disponíveis para curtir (exceto já curtidos e si mesmo)
disponiveis = perfis_df[
    (~perfis_df["login"].isin(ja_curtiu)) & (perfis_df["login"] != usuario)
]

# Mensagem se não houver mais perfis
if disponiveis.empty:
    st.success("Você já viu todos os perfis! Agora é só esperar os matches 🥰")
    st.stop()

# Seleciona um perfil aleatório
perfil = disponiveis.sample(1).iloc[0]

# Exibe perfil
st.subheader(perfil["nome_publico"])
st.text(f"Contato: {perfil['contato']}")
st.text(perfil["descricao"])
st.markdown("**Músicas favoritas:**")
st.text(perfil["musicas"])

# Exibe fotos
fotos = str(perfil["fotos"]).split(";")
for foto_nome in fotos:
    caminho_foto = os.path.join(FOTOS_DIR, foto_nome)
    if os.path.exists(caminho_foto):
        st.image(caminho_foto, use_column_width=True)
    else:
        st.warning(f"Foto {foto_nome} não encontrada.")

# Botões
col1, col2 = st.columns(2)
with col1:
    if st.button("💖 Curtir", key="curtir"):
        novo_like = pd.DataFrame([{"usuario": usuario, "curtido": perfil["login"]}])
        likes_df = pd.concat([likes_df, novo_like], ignore_index=True)
        likes_df.to_csv(LIKES_CSV, index=False)
        st.experimental_rerun()

with col2:
    if st.button("⏩ Pular", key="pular"):
        st.experimental_rerun()
