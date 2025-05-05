import os
import asyncio
import aiohttp
import datetime
from flask import Flask

# === CONFIGURAÇÕES ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FOOTYSTATS_API_KEY = os.getenv("FOOTYSTATS_API_KEY")

if not BOT_TOKEN or not CHAT_ID or not FOOTYSTATS_API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar configurados.")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
MATCHES_URL = f"https://api.football-data-api.com/api/v1/matches?key={FOOTYSTATS_API_KEY}&date_from={datetime.date.today()}"

# Flask app para manter o Render ativo
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot de análise pré-jogo está ativo!"

async def send_telegram_message(session, text):
    try:
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
        await session.get(TELEGRAM_URL, params=payload)
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

async def fetch_matches(session):
    try:
        async with session.get(MATCHES_URL) as resp:
            data = await resp.json()
            return data.get("data", [])
    except Exception as e:
        print("Erro ao buscar partidas:", e)
        return []

async def listar_jogos():
    async with aiohttp.ClientSession() as session:
        await send_telegram_message(session, "
