import os
import pandas as pd

LIKE_DIR = "likes"
UPLOAD_DIR = "uploads"

curtidas = {}
for arquivo in os.listdir(LIKE_DIR):
    if arquivo.endswith("_likes.csv"):
        pessoa = arquivo.replace("_likes.csv", "")
        df = pd.read_csv(os.path.join(LIKE_DIR, arquivo))
        curtidas[pessoa] = df["curtido"].tolist()

def carregar_dados(pessoa):
    try:
        return pd.read_csv(os.path.join(UPLOAD_DIR, pessoa, "dados.csv")).iloc[0]
    except:
        return None

matches = []
for pessoa, curtidos in curtidas.items():
    for alvo in curtidos:
        if alvo in curtidas and pessoa in curtidas[alvo]:
            par = sorted([pessoa, alvo])
            if par not in matches:
                matches.append(par)

match_info = []
for m in matches:
    p1, p2 = m
    d1 = carregar_dados(p1)
    d2 = carregar_dados(p2)

    # Verifica se todos os campos obrigatórios existem
    campos = ["nome_publico", "contato", "descricao", "musicas", "fotos"]
    if not (d1 is not None and d2 is not None):
        print(f"Pulado match entre {p1} e {p2} por dados ausentes.")
        continue
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

pd.DataFrame(match_info).to_csv("matches_completos.csv", index=False)
print("Arquivo 'matches_completos.csv' criado com sucesso!")

