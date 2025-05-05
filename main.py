import os
import asyncio
import aiohttp
import threading
from flask import Flask

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUES = os.getenv("LEAGUE_IDS", "2012").split(",")  # Premier League como default

if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar configurados.")

BASE_URL = "https://api.football-data-api.com"

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot está rodando com sucesso!"

async def send_telegram_message(session, msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": msg}
        await session.get(url, params=params)
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

async def fetch_matches(session):
    matches = []
    for lid in LEAGUES:
        try:
            url = f"{BASE_URL}/league-matches?key={API_KEY}&league_id={lid}"
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get("success"):
                    matches.extend(data.get("data", []))
                elif data.get("error"):
                    print(f"Erro API (liga {lid}):", data["error"])
        except Exception as e:
            print(f"Erro ao buscar dados da liga {lid}:", e)
    return matches

async def analisar_pre_jogo(session, partidas):
    for jogo in partidas:
        status = jogo.get("status", "").lower()
        if status in ("notstarted", "upcoming"):
            home = jogo.get("homeTeam", "Time A")
            away = jogo.get("awayTeam", "Time B")
            league = jogo.get("league_name", "Liga")
            hora = jogo.get("time", "00:00")

            msg = f"\ud83c\udf09 Jogo encontrado:\n\ud83c\udfdf\ufe0f {home} x {away}\n\u23f0 Horário: {hora}\n\ud83c\udfc6 Liga: {league}"
            await send_telegram_message(session, msg)

async def main_async():
    async with aiohttp.ClientSession() as session:
        await send_telegram_message(session, "\ud83d\ude80 Bot ativado e buscando jogos do dia...")
        partidas = await fetch_matches(session)
        if partidas:
            await analisar_pre_jogo(session, partidas)
        else:
            await send_telegram_message(session, "\u26a0\ufe0f Nenhuma partida ativa ou agendada nas ligas selecionadas.")

# Roda o bot ao subir o render
if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))), daemon=True).start()
    asyncio.run(main_async())
