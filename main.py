import os
import asyncio
import aiohttp
import threading
from flask import Flask
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "")

if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar configurados.")

league_ids = [lid.strip() for lid in LEAGUE_IDS.split(",") if lid.strip()]
BASE_URL = "https://api.football-data-api.com"
league_urls = [f"{BASE_URL}/league-matches?key={API_KEY}&league_id={lid}" for lid in league_ids]

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot ativo!"

async def send_message(session, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": text}
        await session.get(url, params=params)
    except Exception as e:
        print(f"[ERRO Telegram] {e}")

async def listar_jogos_do_dia(session):
    hoje = datetime.now().date()
    jogos_hoje = []

    for url in league_urls:
        try:
            async with session.get(url) as resp:
                data = await resp.json()
                partidas = data.get("data", [])
                for jogo in partidas:
                    timestamp = jogo.get("date_unix", 0)
                    data_jogo = datetime.fromtimestamp(timestamp)
                    if data_jogo.date() == hoje:
                        hora = data_jogo.strftime('%H:%M')
                        time_a = jogo.get("homeTeam", jogo.get("home_name", "Time A"))
                        time_b = jogo.get("awayTeam", jogo.get("away_name", "Time B"))
                        jogos_hoje.append(f"- {time_a} x {time_b} às {hora}")
        except Exception as e:
            print(f"[ERRO ao buscar jogos] {e}")

    if jogos_hoje:
        mensagem = "📅 *Jogos de hoje:*\n" + "\n".join(jogos_hoje)
        await send_message(session, mensagem)
    else:
        await send_message(session, "📭 Nenhum jogo encontrado para hoje nas ligas configuradas.")

async def executar():
    async with aiohttp.ClientSession() as session:
        await send_message(session, "🚀 Bot ativado e listando jogos do dia...")
        await listar_jogos_do_dia(session)

def iniciar_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=iniciar_flask, daemon=True).start()
    asyncio.run(executar())
