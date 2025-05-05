import os
import threading
import asyncio
import aiohttp
from datetime import datetime, timedelta
from flask import Flask

# Configurações a partir de variáveis de ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS")  # Ex: "2012,2015,2023"

if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar configurados.")

league_ids = [lid.strip() for lid in LEAGUE_IDS.split(",") if lid.strip()]
BASE_URL = "https://api.football-data-api.com"

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot está ativo!"

async def send_telegram_message(session, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text}
    try:
        await session.get(url, params=params)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

async def fetch_today_matches(session):
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    all_matches = []
    for lid in league_ids:
        url = f"{BASE_URL}/league-matches?key={API_KEY}&league_id={lid}&date_from={today_str}&date_to={today_str}"
        try:
            async with session.get(url) as resp:
                data = await resp.json()
        except Exception as e:
            print(f"Erro na liga {lid}: {e}")
            continue

        if data and "data" in data:
            all_matches.extend(data["data"])
        elif data and "error" in data:
            print(f"Erro da API para liga {lid}: {data['error']}")
    return all_matches

async def listar_jogos_do_dia():
    async with aiohttp.ClientSession() as session:
        await send_telegram_message(session, "
