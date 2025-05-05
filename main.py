import os
import threading
import asyncio
import aiohttp
import datetime
from dateutil.parser import parse
from flask import Flask

# === Variáveis de ambiente ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS")

if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar configurados.")

# Liga padrao se não houver
league_ids = [lid.strip() for lid in LEAGUE_IDS.split(",") if lid.strip()] if LEAGUE_IDS else ["2012"]
BASE_URL = "https://api.football-data-api.com"
LEAGUE_URLS = [f"{BASE_URL}/league-matches?key={API_KEY}&league_id={lid}" for lid in league_ids]

# Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot de análise pré-jogo está ativo."

async def send_telegram(session, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": text}
        await session.get(url, params=params)
    except Exception as e:
        print(f"[ERRO Telegram] {e}")

async def fetch_games(session):
    all_matches = []
    for url in LEAGUE_URLS:
        try:
            async with session.get(url) as resp:
                data = await resp.json()
                if data and "data" in data:
                    all_matches.extend(data["data"])
        except Exception as e:
            print(f"[ERRO API] {e}")
    return all_matches

async def process_games(session, games):
    hoje = datetime.date.today()
    encontrados = 0
    for jogo in games:
        data_partida = jogo.get("date")
        if not data_partida:
            continue
        try:
            data_jogo = parse(data_partida).date()
            if data_jogo == hoje:
                home = jogo.get("homeTeam", "Time A")
                away = jogo.get("awayTeam", "Time B")
                status = jogo.get("status", "-")
                msg = f"
