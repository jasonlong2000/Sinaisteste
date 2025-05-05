import os
import asyncio
import aiohttp
import datetime
from flask import Flask
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "")

if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar definidos.")

league_ids = [lid.strip() for lid in LEAGUE_IDS.split(",") if lid.strip()]
if not league_ids:
    league_ids = ["2012"]  # Premier League como padrão

BASE_URL = "https://api.football-data-api.com"
league_urls = [f"{BASE_URL}/league-matches?key={API_KEY}&league_id={lid}" for lid in league_ids]

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot de debug ativo!"

async def send_telegram(session, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        await session.get(url, params={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

async def verificar_ligas():
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    async with aiohttp.ClientSession() as session:
        await send_telegram(session, f"🧪 Iniciando verificação de jogos ({hoje})")
        for url in league_urls:
            try:
                async with session.get(url) as resp:
                    data = await resp.json()
                    liga_id = url.split("=")[-1]
                    if "data" in data:
                        jogos = data["data"]
                        texto = f"⚽ Liga {liga_id}: {len(jogos)} jogos encontrados\n"
                        for jogo in jogos:
                            status = jogo.get("status", "indefinido")
                            data_jogo = jogo.get("date", "sem data")
                            texto += f"• {data_jogo} | status: {status}\n"
                        await send_telegram(session, texto)
                    else:
                        await send_telegram(session, f"⚠️ Erro ao buscar liga {liga_id}: {data.get('error', 'sem detalhes')}")
            except Exception as e:
                await send_telegram(session, f"❌ Erro ao acessar API da liga {url}: {e}")

def start_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(verificar_ligas())

if __name__ == "__main__":
    threading.Thread(target=start_loop).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
