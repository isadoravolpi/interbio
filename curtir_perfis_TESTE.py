import streamlit as st
import os
import pandas as pd
import random

UPLOAD_DIR = "uploads"
LIKE_DIR = "likes"
os.makedirs(LIKE_DIR, exist_ok=True)

st.title("🔥 MATCH - TINDER DA CEÓ")

usuario = st.text_input("Digite seu nome de login privado (exatamente como cadastrou)")
if not usuario:
    st.stop()

like_path = f"{LIKE_DIR}/{usuario}_likes.csv"
if os.path.exists(like_path):
    ja_curtiu = pd.read_csv(like_path)["curtido"].tolist()
else:
    ja_curtiu = []

# Gera e guarda a lista embaralhada de perfis restantes apenas uma vez
if "restantes" not in st.session_state:
    participantes = [p for p in os.listdir(UPLOAD_DIR) if p != usuario]
    random.shuffle(participantes)
    st.session_state.restantes = [p for p in participantes if p not in ja_curtiu]
    st.session_state.indice_perfil = 0

restantes = st.session_state.restantes

if st.session_state.indice_perfil >= len(restantes):
    st.success("Você já viu todos os perfis! Agora é só esperar os matches 🥰")
    st.stop()

perfil = restantes[st.session_state.indice_perfil]
perfil_dir = os.path.join(UPLOAD_DIR, perfil)

dados_path = os.path.join(perfil_dir, "dados.csv")

# Verifica se o arquivo dados.csv existe
if not os.path.exists(dados_path):
    st.warning(f"Perfil de {perfil} não possui dados.csv. Pulando...")
    st.session_state.indice_perfil += 1
    st.experimental_rerun()

# Tenta carregar os dados com proteção
try:
    dados = pd.read_csv(dados_path).iloc[0]
except Exception as e:
    st.warning(f"Erro ao carregar dados de {perfil}. Pulando...\n{e}")
    st.session_state.indice_perfil += 1
    st.experimental_rerun()

# Verifica se o perfil tem os campos obrigatórios
campos_obrigatorios = ["nome_publico", "descricao", "musicas", "fotos"]
if any(c not in dados for c in campos_obrigatorios):
    st.warning(f"Perfil de {perfil} incompleto. Pulando...")
    st.session_state.indice_perfil += 1
    st.rerun()

st.subheader(dados["nome_publico"])
st.text(dados["descricao"])
st.text("Músicas favoritas:")
st.text(dados["musicas"])

for foto_nome in dados["fotos"].strip("[]").replace("'", "").split(", "):
    caminho_foto = os.path.join(perfil_dir, foto_nome)
    if os.path.exists(caminho_foto):
        st.image(caminho_foto, use_column_width=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("💖 Curtir"):
        novo_like = pd.DataFrame([{"curtido": perfil}])
        if os.path.exists(like_path):
            novo_like.to_csv(like_path, mode='a', header=False, index=False)
        else:
            novo_like.to_csv(like_path, index=False)
        st.session_state.indice_perfil += 1
        st.rerun()

with col2:
    if st.button("⏩ Pular"):
        st.session_state.indice_perfil += 1
        st.rerun()
