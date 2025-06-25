import streamlit as st
import shutil
import os

st.title("🧼 Reiniciar o TINDER DA CEÓ")

st.warning("CUIDADO! Essa ação irá apagar todos os dados coletados, curtidas e matches.")

if st.button("🔥 Apagar tudo e recomeçar do zero"):
    shutil.rmtree("uploads", ignore_errors=True)
    shutil.rmtree("likes", ignore_errors=True)
    if os.path.exists("matches_completos.csv"):
        os.remove("matches_completos.csv")

    st.success("Tudo apagado com sucesso! O app foi reiniciado 🧼")
else:
    st.info("Nada foi apagado ainda. Clique no botão acima para executar a limpeza.")
