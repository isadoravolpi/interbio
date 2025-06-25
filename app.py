import streamlit as st

st.set_page_config(page_title="Tinder CEÓ", page_icon="💘")

st.title("💘 TINDER DA CEÓ")
st.markdown("Bem-vindo(a)! Use o menu lateral para navegar entre as páginas disponíveis.")

# Mapeamento de páginas: nome amigável → nome do módulo
paginas = {
    "💖 Curtir Perfis": "curtir_perfis",
    "🤖 Gerar Matches": "gerar_matches_TESTE",
    "💍 Ver Meus Matches": "ver_meus_matches_TESTE",
    "📊 Visualizar Dados": "visualizar_dados",
    "🧹 Resetar App": "reset_app"
}

escolhida = st.sidebar.selectbox("Navegação", list(paginas.keys()))

# Tenta importar o módulo correspondente
try:
    exec(f"import {paginas[escolhida]}")
except Exception as e:
    st.error(f"Erro ao carregar a página **{escolhida}**.")
    st.exception(e)
