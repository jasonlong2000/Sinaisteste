import os
import asyncio
import aiohttp
from flask import Flask
from telegram import Bot
import threading

# === Configurações ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FOOTYSTATS_API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "2012")  # Liga padrão Premier League

if not BOT_TOKEN or not CHAT_ID or not FOOTYSTATS_API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar definidos.")

league_ids = [lid.strip() for lid in LEAGUE_IDS.split(",") if lid.strip()]
BASE_URL = "https://api.football-data-api.com"
league_urls = [f"{BASE_URL}/league-matches?key={FOOTYSTATS_API_KEY}&league_id={lid}" for lid in league_ids]

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

@app.route("/")
def index():
    return "Bot está online!"

async def send_telegram(session, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        await session.get(url, params={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Erro ao enviar:", e)

async def listar_jogos():
    async with aiohttp.ClientSession() as session:
        await send_telegram(session, "🚀 Bot de verificação de partidas ativado!")
        for url in league_urls:
            try:
                async with session.get(url) as resp:
                    data = await resp.json()
            except Exception as e:
                print(f"Erro ao buscar {url}: {e}")
                continue

            jogos = data.get("data", [])
            if not jogos:
                await send_telegram(session, "📭 Nenhum jogo encontrado nessa liga.")
                continue

            await send_telegram(session, f"📊 {len(jogos)} jogo(s) encontrados:\n")

            for jogo in jogos:
                casa = jogo.get("homeTeam", "Time A")
                fora = jogo.get("awayTeam", "Time B")
                status = jogo.get("status", "indefinido").upper()
                minuto = jogo.get("minute", "-")
                texto = f"🏟️ {casa} x {fora}\nStatus: {status} | Minuto: {minuto}"
                await send_telegram(session, texto)
                await asyncio.sleep(0.5)

def rodar_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listar_jogos())

if __name__ == "__main__":
    thread = threading.Thread(target=rodar_bot, daemon=True)
    thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
