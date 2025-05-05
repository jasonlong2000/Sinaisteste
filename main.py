import os
import threading
import asyncio
import aiohttp
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS")

if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar configurados.")

league_ids = [lid.strip() for lid in LEAGUE_IDS.split(",") if lid.strip()] if LEAGUE_IDS else ["2012"]

BASE_URL = "https://api.football-data-api.com"
league_urls = [f"{BASE_URL}/league-matches?key={API_KEY}&league_id={lid}" for lid in league_ids]

app = Flask(__name__)

@app.route("/")
def index():
    return "Seu serviço está ativo! ✅"

async def send_telegram_message(session, text: str):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": text}
        await session.get(url, params=params)
    except Exception as e:
        print(f"[ERRO] Falha ao enviar mensagem: {e}")

async def fetch_matches(session) -> list:
    all_matches = []
    for url in league_urls:
        try:
            async with session.get(url) as resp:
                data = await resp.json()
        except Exception as e:
            print(f"[ERRO] Falha ao obter dados da URL {url}: {e}")
            data = None
        if data and "data" in data:
            all_matches.extend(data["data"])
        elif data and "error" in data:
            print(f"[ERRO] API FootyStats retornou erro: {data.get('error')}")
    return all_matches

async def process_and_send_signals(session, matches: list):
    for match in matches:
        status = match.get("status", "").lower()
        if status not in ("inplay", "playing"):
            continue
        home = match.get("homeTeam", "Time A")
        away = match.get("awayTeam", "Time B")
        msg = f"\ud83c\udf1f {home} x {away}\nStatus: {status.upper()} | Minuto: -"
        await send_telegram_message(session, msg)

async def main_loop_async():
    async with aiohttp.ClientSession() as session:
        await send_telegram_message(session, "\u2708\ufe0f Bot iniciado com sucesso e buscando jogos de hoje...")
        matches = await fetch_matches(session)
        if matches:
            await process_and_send_signals(session, matches)
        else:
            await send_telegram_message(session, "\u26a0\ufe0f Nenhuma partida ativa ou agendada nas ligas selecionadas.")

        await asyncio.sleep(5)  # para testes (ajuste para execução recorrente conforme necessidade)

def start_background_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_loop_async())
    except Exception as e:
        print(f"[ERRO] Loop de background encerrou: {e}")

thread = threading.Thread(target=start_background_loop, daemon=True)
thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
