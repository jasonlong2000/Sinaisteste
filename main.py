import os
import asyncio
import aiohttp
from datetime import datetime
from flask import Flask
from telegram import Bot

# Configs via Render Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUES = os.getenv("LEAGUE_IDS", "2012,2027,2015,2030,2016,2031,2013,2032,2014,2033").split(",")

if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar configurados.")

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot de jogos do dia está ativo!"

BASE_URL = "https://api.football-data-api.com"

async def send_message(session, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text}
        async with session.post(url, data=payload) as resp:
            await resp.text()
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

async def fetch_league_matches(session, league_id):
    url = f"{BASE_URL}/league-matches?key={API_KEY}&league_id={league_id}"
    try:
        async with session.get(url) as resp:
            return await resp.json()
    except Exception as e:
        print(f"Erro ao buscar dados da liga {league_id}:", e)
        return {}

async def buscar_jogos_do_dia():
    hoje = datetime.now().strftime("%Y-%m-%d")
    mensagens = []
    async with aiohttp.ClientSession() as session:
        await send_message(session, "🚀 Bot iniciado com sucesso e buscando jogos de hoje...")

        for liga in LEAGUES:
            data = await fetch_league_matches(session, liga)
            jogos = data.get("data", [])
            jogos_hoje = [j for j in jogos if j.get("status") == "not_started" and j.get("date", "").startswith(hoje)]

            if jogos_hoje:
                for jogo in jogos_hoje:
                    home = jogo.get("homeTeam", "Time A")
                    away = jogo.get("awayTeam", "Time B")
                    hora = jogo.get("time", "-")
                    mensagem = f"🌟 {home} x {away}\nStatus: NOT STARTED | Horário: {hora}"
                    mensagens.append(mensagem)
            else:
                mensagens.append(f"🌟 Liga {liga}: Nenhum jogo programado para hoje")

        for msg in mensagens:
            await send_message(session, msg)
            await asyncio.sleep(1)

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000))), daemon=True).start()
    asyncio.run(buscar_jogos_do_dia())
