import requests
import time
import json
from datetime import datetime
from telegram import Bot

# Configurações
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
CHAT_ID = "-1002675165012"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"

LEAGUE_IDS = {
    12321: "Champions League",
    2033: "Premier League",
    2022: "Brasileirão",
    2034: "Serie A",
    2040: "La Liga"
}

DATA_FILE = "enviados.json"
INTERVALO = 6 * 60 * 60  # 6 horas

bot = Bot(token=BOT_TOKEN)

# Carregar jogos já enviados
try:
    with open(DATA_FILE, "r") as f:
        enviados = set(json.load(f))
except:
    enviados = set()

def salvar_enviados():
    with open(DATA_FILE, "w") as f:
        json.dump(list(enviados), f)

def fetch_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        response = requests.get(url)
        return response.json().get("data", [])
    except Exception as e:
        print(f"Erro ao buscar dados da liga {league_id}: {e}")
        return []

def formatar_jogo(jogo):
