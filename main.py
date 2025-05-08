import requests

API_KEY = "6810ea1e7c44dab18f4fc039b73e8dd2"
HEADERS = {"x-apisports-key": API_KEY}
URL = "https://v3.football.api-sports.io/leagues"

res = requests.get(URL, headers=HEADERS)
ligas = res.json()["response"]

for liga in ligas:
    nome = liga["league"]["name"]
    id_liga = liga["league"]["id"]
    pais = liga["country"]["name"]
    print(f"ID: {id_liga} | {nome} ({pais})")
