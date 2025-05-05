import requests
import time
import os
import threading
from telegram import Bot
from flask import Flask

# === CONFIGURAÇÕES ===
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
CHAT_ID = os.getenv("CHAT_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "2012").split(",")  # Premier League como exemplo

bot = Bot(token=BOT_TOKEN)

# === APP FLASK PARA MANTER O BOT ATIVO ===
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot está ativo e funcionando!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# === FUNÇÕES DE COLETA E ENVIO ===
def fetch_today_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"Erro ao buscar dados da liga {league_id}: {e}")
        return []

def format_match(match):
    home = match.get("home_name", "Time A")
    away = match.get("away_name", "Time B")
    status = match.get("status", "-").upper()
    minute = match.get("minute", "-")
    return f"
