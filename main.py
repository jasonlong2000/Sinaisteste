import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# Configurações
API_KEY = "6810ea1e7c44dab18f4fc039b73e8dd2"
API_URL = "https://v3.football.api-sports.io/fixtures"

# Ligas permitidas (País + Nome da Liga)
LIGAS_PERMITIDAS = [
    {"country": "Belgium", "name": "Pro League"},
    {"country": "Brazil",  "name": "Serie A"},
    {"country": "Brazil",  "name": "Copa do Brasil"},
    {"country": "Brazil",  "name": "Serie B"},
    {"country": "Brazil",  "name": "Paulista"},
    {"country": "Brazil",  "name": "Gaucho 1"},
    {"country": "Bulgaria","name": "First League"},
    {"country": "England", "name": "Premier League"},
    {"country": "England", "name": "Community Shield"},
    {"country": "England", "name": "Championship"},
    {"country": "England", "name": "League Cup"},
    {"country": "England", "name": "Premier League Summer Series"},
    {"country": "England", "name": "EFL League One"},
    {"country": "Europe",  "name": "UEFA Champions League"},
    {"country": "Europe",  "name": "UEFA Europa League"},
    {"country": "Europe",  "name": "UEFA Super Cup"},
    {"country": "Europe",  "name": "UEFA Europa Conference League"},
    {"country": "France",  "name": "Ligue 1"},
    {"country": "France",  "name": "Coupe de la Ligue"},
    {"country": "Germany", "name": "Bundesliga"},
    {"country": "International", "name": "UEFA Euro Championship"},
    {"country": "International", "name": "FIFA Confederations Cup"},
    {"country": "International", "name": "UEFA Euro Qualifiers"},
    {"country": "International", "name": "UEFA Nations League"},
    {"country": "International", "name": "FIFA Club World Cup"},
    {"country": "International", "name": "Copa America"},
    {"country": "International", "name": "Olympics"},
    {"country": "Italy",   "name": "Serie A"},
    {"country": "Spain",   "name": "La Liga"},
    {"country": "Spain",   "name": "Copa del Rey"},
    {"country": "Spain",   "name": "Supercopa de Espana"},
    {"country": "USA",     "name": "MLS"},
    {"country": "South America", "name": "Copa Libertadores"},
    {"country": "South America", "name": "Copa Sudamericana"},
    {"country": "South America", "name": "CONMEBOL Recopa Sudamericana"}
]

def buscar_jogos_do_dia():
    hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d")
    params = {
        "date": hoje,
        "status": "NS",  # Only not started games
        "timezone": "America/Sao_Paulo"
    }
    headers = {
        "x-apisports-key": API_KEY
    }

    try:
        res = requests.get(API_URL, params=params, headers=headers, timeout=15)
        res.raise_for_status()
        return res.json().get("response", [])
    except Exception as e:
        print(f"Erro ao buscar jogos: {e}")
        return []

def exibir_jogos(jogos):
    if not jogos:
        print("❌ Nenhum jogo encontrado para hoje.")
        return

    print("🟢 PRÉ-JOGOS DO DIA (Somente ligas permitidas):\n")

    for jogo in jogos:
        league = jogo["league"]
        fixture = jogo["fixture"]
        teams = jogo["teams"]

        liga_pais = {"country": league["country"], "name": league["name"]}
        if liga_pais not in LIGAS_PERMITIDAS:
            continue

        home = teams["home"]["name"]
        away = teams["away"]["name"]
        estadio = fixture["venue"]["name"]
        data_hora_str = fixture["date"]

        try:
            data_hora = datetime.fromisoformat(data_hora_str)
            data_fmt = data_hora.strftime("%d/%m/%Y %H:%M")
        except:
            data_fmt = data_hora_str

        print(f"{league['country']} - {league['name']}: {home} x {away} - {data_fmt} | Estádio: {estadio}")

if __name__ == "__main__":
    jogos_do_dia = buscar_jogos_do_dia()
    exibir_jogos(jogos_do_dia)
