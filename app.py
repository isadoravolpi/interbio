import streamlit as st

st.set_page_config(page_title="Tinder CEÓ")

pagina = st.sidebar.selectbox("Navegação", ["tinder_ceo_TESTE", "curtir_perfis_TESTE", "ver_meus_matches_TESTE", "visualizar_dados"])

if pagina == "tinder_ceo_TESTE":
    import tinder_ceo_TESTE
elif pagina == "curtir_perfis_TESTE":
    import curtir_perfis_TESTE
elif pagina == "ver_meus_matches_TESTE":
    import ver_meus_matches_TESTE
elif pagina == "visualizar_dados":
    import visualizar_dados
