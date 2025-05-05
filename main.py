import os
import asyncio
import aiohttp
from flask import Flask
import threading

# === CONFIGURAÇÕES ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "").split(",")

if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar configurados.")

# === URLs ===
BASE_URL = "https://api.football-data-api.com"
LEAGUE_URLS = [f"{BASE_URL}/league-matches?key={API_KEY}&league_id={lid.strip()}" for lid in LEAGUE_IDS if lid.strip()]

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot pré-jogo está ativo!"

async def send_message(session, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    await session.get(url, params={"chat_id": CHAT_ID, "text": text})

async def fetch_matches(session):
    matches = []
    for url in LEAGUE_URLS:
        try:
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get("success"):
                    matches.extend(data.get("data", []))
        except Exception as e:
            print(f"Erro ao buscar dados: {e}")
    return matches

async def analisar_jogos(session):
    jogos = await fetch_matches(session)
    if not jogos:
        await send_message(session, "📭 Nenhum jogo encontrado para hoje nas ligas configuradas.")
        return

    await send_message(session, f"🚀 Bot ativado e listando jogos do dia ({len(jogos)} jogo(s) encontrados):")

    for jogo in jogos:
        status = jogo.get("status", "-").upper()
        minuto = jogo.get("minute", "-") or jogo.get("mins", "-")
        casa = jogo.get("home_name", "Time A")
        fora = jogo.get("away_name", "Time B")

        texto = f"\ud83c\udfdf\ufe0f {casa} x {fora}\nStatus: {status} | Minuto: {minuto}"
        await send_message(session, texto)

async def executar():
    async with aiohttp.ClientSession() as session:
        await send_message(session, "\ud83d\udd34 Bot de análise pré-jogo ativado. Verificando oportunidades...")
        await analisar_jogos(session)

def flask_background():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=flask_background).start()
    asyncio.run(executar())
