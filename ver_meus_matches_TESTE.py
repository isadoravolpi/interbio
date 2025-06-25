import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# Autenticação
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

# Planilha
PLANILHA = "TINDER_CEO_PERFIS"
sheet = client.open(PLANILHA)
matches_ws = sheet.worksheet("matches")

# Função para converter link em URL de visualização
def drive_link_para_visualizacao(link):
    if "id=" in link:
        file_id = link.split("id=")[-1]
        return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return link

# Interface
st.title("💍 Veja seus Matches - TINDER DA CEÓ")

usuario = st.text_input("Digite seu nome de login privado (igual cadastrado)")
if not usuario:
    st.stop()

# Carrega matches
dados = matches_ws.get_all_values()
cabecalho, linhas = dados[0], dados[1:]
df = pd.DataFrame(linhas, columns=cabecalho)

# Filtra matches do usuário
meus_matches = df[df["eu"] == usuario]

if meus_matches.empty:
    st.info("Ainda não rolou nenhum match 😢 Mas vai acontecer!")
    st.stop()

st.success(f"Você teve {len(meus_matches)} match(es)! 🎉")

# Mostra cada match
for _, row in meus_matches.iterrows():
    st.subheader(f"{row['match_nome_publico']} 💖")
    st.text(f"Contato: {row['contato']}")
    st.text(f"Descrição: {row['descricao']}")
    st.markdown("🎵 **Músicas favoritas:**")
    st.text(row["musicas"])

    fotos = [f.strip() for f in row["fotos"].split(",") if f.strip().startswith("http")]
    if fotos:
        st.markdown("📸 **Fotos do match:**")
        cols = st.columns(3)
        for i, link in enumerate(fotos):
            with cols[i % 3]:
                st.markdown(
                    f'<img src="{drive_link_para_visualizacao(link)}" style="width:100%; border-radius: 10px; margin-bottom:10px;">',
                    unsafe_allow_html=True
                )
    st.markdown("---")
