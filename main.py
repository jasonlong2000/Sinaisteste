import requests
import time
import os
from telegram import Bot
from datetime import datetime
from flask import Flask
from threading import Thread

API_KEY = os.getenv("FOOTYSTATS_API_KEY")
CHAT_ID = os.getenv("CHAT_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "2012").split(",")

bot = Bot(token=BOT_TOKEN)
dispatched_matches = set()

# === FLASK para manter ativo no Render ===
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot ativo!"

def fetch_today_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id.strip()}"
    try:
        response = requests.get(url)
        return response.json().get("data", [])
    except Exception as e:
        print(f"Erro na liga {league_id}: {e}")
        return []

def format_match(match):
    home = match.get("home_name", "Time A")
    away = match.get("away_name", "Time B")
    status = match.get("status", "-").upper()
    minute = match.get("minute", "-")
    timestamp = match.get("date_unix", 0)
    date_str = datetime.fromtimestamp(timestamp).strftime('%d/%m') if timestamp else "?"
    hour_str = datetime.fromtimestamp(timestamp).strftime('%H:%M') if timestamp else "?"
    league = match.get("competition_name", "Liga")
    phase = match.get("stage_name", "Fase desconhecida")

    return (
        f"
