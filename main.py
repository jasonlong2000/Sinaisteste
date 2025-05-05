import os
import aiohttp
import asyncio
from datetime import datetime
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS")

if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar configurados.")

league_ids = [lid.strip() for lid in LEAGUE_IDS.split(",") if lid.strip()]
if not league_ids:
    league_ids = ["2012"]  # Premier League como fallback

BASE_URL = "https://api.football-data-api.com"
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot de análise pré-jogo está ativo."

async def send_message(session, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        await session.post(url, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

async def buscar_partidas():
    async with aiohttp.ClientSession() as session:
        await send_message(session, "🚀 Bot ativado e buscando jogos de hoje...")
        hoje = datetime.utcnow().date()
        jogos_encontrados = []

        for lid in league_ids:
            url = f"{BASE_URL}/league-matches?key={API_KEY}&league_id={lid}"
            try:
                async with session.get(url) as resp:
                    data = await resp.json()
            except Exception as e:
                print(f"Erro ao acessar liga {lid}: {e}")
                continue

            if data.get("success") and "data" in data:
                for jogo in data["data"]:
                    try:
                        status = jogo.get("status", "").lower()
                        dt = datetime.utcfromtimestamp(jogo.get("date_unix", 0)).date()

                        if dt == hoje and status in ["not_started", "fixture"]:
                            home = jogo.get("homeTeam") or jogo.get("home_name", "Time A")
                            away = jogo.get("awayTeam") or jogo.get("away_name", "Time B")
                            liga = jogo.get("league_name", "Liga")
                            hora = datetime.utcfromtimestamp(jogo.get("date_unix", 0)).strftime("%H:%M")
                            jogos_encontrados.append(f"🌟 {home} x {away} | Início: {hora} | {liga}")
                    except:
                        continue

        if jogos_encontrados:
            await send_message(session, f"🔹 {len(jogos_encontrados)} jogo(s) encontrados para hoje:")
            for jogo in jogos_encontrados:
                await send_message(session, jogo)
        else:
            await send_message(session, "📍 Nenhum jogo agendado para hoje nas ligas configuradas.")

if __name__ == "__main__":
    asyncio.run(buscar_partidas())
