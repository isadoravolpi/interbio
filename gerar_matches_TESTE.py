import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# Autenticação
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("secrets.json", scope)  # Troque pelo caminho correto
client = gspread.authorize(creds)

# Planilha
sheet = client.open("TINDER_CEO_PERFIS")
perfis_ws = sheet.worksheet("perfis")
likes_ws = sheet.worksheet("likes")

# Carrega dados
df_perfis = pd.DataFrame(perfis_ws.get_all_records())
df_likes = pd.DataFrame(likes_ws.get_all_records())

# Normaliza
df_perfis.columns = df_perfis.columns.str.strip()
df_likes.columns = df_likes.columns.str.strip()

# Cria dicionário de curtidas
curtidas_dict = df_likes.groupby("quem_curtiu")["quem_foi_curtido"].apply(list).to_dict()

# Detecta matches
matches = set()
for pessoa, curtidos in curtidas_dict.items():
    for alvo in curtidos:
        if alvo in curtidas_dict and pessoa in curtidas_dict[alvo]:
            matches.add(tuple(sorted((pessoa, alvo))))

# Gera lista com dados completos
match_info = []
for p1, p2 in matches:
    d1 = df_perfis[df_perfis["login"] == p1].iloc[0].to_dict()
    d2 = df_perfis[df_perfis["login"] == p2].iloc[0].to_dict()
    campos = ["nome_publico", "contato", "descricao", "musicas", "fotos"]

    if not all(c in d1 and c in d2 for c in campos):
        print(f"Pulado match entre {p1} e {p2} por dados incompletos.")
        continue

    match_info.append({
        "eu": p1,
        "match_login": p2,
        "match_nome_publico": d2["nome_publico"],
        "contato": d2["contato"],
        "descricao": d2["descricao"],
        "musicas": d2["musicas"],
        "fotos": d2["fotos"]
    })
    match_info.append({
        "eu": p2,
        "match_login": p1,
        "match_nome_publico": d1["nome_publico"],
        "contato": d1["contato"],
        "descricao": d1["descricao"],
        "musicas": d1["musicas"],
        "fotos": d1["fotos"]
    })

# Salva CSV
pd.DataFrame(match_info).to_csv("matches_completos.csv", index=False)
print("Arquivo 'matches_completos.csv' criado com sucesso!")
