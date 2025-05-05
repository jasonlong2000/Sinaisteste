import os
import asyncio
import aiohttp
import threading
from flask import Flask

# === CONFIGURAÇÕES ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS")

if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar definidos.")

league_ids = [lid.strip() for lid in (LEAGUE_IDS or "2012").split(",") if lid.strip()]

BASE_URL = "https://api.football-data-api.com"
league_urls = [f"{BASE_URL}/league-matches?key={API_KEY}&league_id={lid}" for lid in league_ids]

app = Flask(__name__)

@app.route("/")
def index():
    return "Servidor ativo"

async def send_telegram(session, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text}
    try:
        await session.get(url, params=params)
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

async def buscar_partidas(session):
    partidas = []
    for url in league_urls:
        try:
            async with session.get(url) as resp:
                data = await resp.json()
                if "data" in data:
                    partidas.extend(data["data"])
        except Exception as e:
            print("Erro ao buscar:", e)
    return partidas

async def analisar_e_enviar(session, partidas):
    for partida in partidas:
        home = partida.get("homeTeam", "Time A")
        away = partida.get("awayTeam", "Time B")
        status = partida.get("status", "-").upper()
        minute = partida.get("minute", "-") or partida.get("mins", "-")

        msg = f"\ud83c\udfdf\ufe0f {home} x {away}\nStatus: {status} | Minuto: {minute}"
        await send_telegram(session, msg)

async def rotina():
    async with aiohttp.ClientSession() as session:
        await send_telegram(session, "\ud83d\ude80 Bot ativado e buscando jogos do dia...")
        partidas = await buscar_partidas(session)
        if partidas:
            await analisar_e_enviar(session, partidas)
        else:
            await send_telegram(session, "\ud83d\udccd Nenhum jogo agendado para hoje nas ligas configuradas.")

async def agendador():
    while True:
        await rotina()
        await asyncio.sleep(21600)  # 6 horas

def iniciar_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(agendador())

if __name__ == "__main__":
    threading.Thread(target=iniciar_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
