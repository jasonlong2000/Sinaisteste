import os
import aiohttp
import asyncio
from flask import Flask
import threading

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS")  # Ex: "2012, 2015, 2019"

if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar configurados.")

league_ids = [lid.strip() for lid in LEAGUE_IDS.split(",") if lid.strip()]
if not league_ids:
    league_ids = ["2012"]  # fallback para Premier League

BASE_URL = "https://api.football-data-api.com"
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot de análise pré-jogo está ativo!"

async def send_message(session, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        await session.post(url, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

async def fetch_matches(session):
    matches = []
    for lid in league_ids:
        url = f"{BASE_URL}/league-matches?key={API_KEY}&league_id={lid}"
        try:
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get("success") and data.get("data"):
                    matches.extend(data["data"])
        except Exception as e:
            print(f"Erro ao buscar jogos da liga {lid}: {e}")
    return matches

async def listar_partidas(session):
    await send_message(session, "🚀 Bot ativado e buscando jogos do dia...")
    jogos = await fetch_matches(session)
    if not jogos:
        await send_message(session, "📍 Nenhum jogo agendado para hoje nas ligas configuradas.")
        return

    encontrados = 0
    for match in jogos:
        status = match.get("status", "")
        if status.lower() in ["not_started", "inplay"]:
            home = match.get("homeTeam") or match.get("home_name") or "Time A"
            away = match.get("awayTeam") or match.get("away_name") or "Time B"
            minute = match.get("minute") or "-"
            msg = f"🏟 {home} x {away}\nStatus: {status.upper()} | Minuto: {minute}"
            await send_message(session, msg)
            encontrados += 1

    if encontrados == 0:
        await send_message(session, "⚠️ Nenhuma partida ativa ou agendada nas ligas selecionadas.")

async def start_bot():
    async with aiohttp.ClientSession() as session:
        await listar_partidas(session)

def flask_thread():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    threading.Thread(target=flask_thread, daemon=True).start()
    asyncio.run(start_bot())
