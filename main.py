import requests
import time
from telegram import Bot
from datetime import datetime

# Configurações fixas para Champions League
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"
CHAMPIONS_LEAGUE_ID = 12321  # ID da UEFA Champions League

bot = Bot(token=BOT_TOKEN)
dispatched_matches = set()

def fetch_today_matches():
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={CHAMPIONS_LEAGUE_ID}"
    try:
        response = requests.get(url, timeout=10)
        return response.json().get("data", [])
    except Exception as e:
        print(f"Erro ao buscar dados da Champions League: {e}")
        return []

def format_match(match):
    home = match.get("home_name", "Time A")
    away = match.get("away_name", "Time B")
    status = match.get("status", "-").upper()
    minute = match.get("minute", "-")
    timestamp = match.get("date_unix", 0)
    date_str = datetime.fromtimestamp(timestamp).strftime('%d/%m') if timestamp else "?"
    hour_str = datetime.fromtimestamp(timestamp).strftime('%H:%M') if timestamp else "?"
    stage = match.get("competition_stage_name", "Fase")
    return f"
