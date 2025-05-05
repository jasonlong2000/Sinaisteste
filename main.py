import os
import requests
from datetime import datetime
from telegram import Bot
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS")

if not BOT_TOKEN or not CHAT_ID or not API_KEY or not LEAGUE_IDS:
    raise RuntimeError("BOT_TOKEN, CHAT_ID, FOOTYSTATS_API_KEY e LEAGUE_IDS devem estar configurados.")

league_ids = [lid.strip() for lid in LEAGUE_IDS.split(",") if lid.strip()]
BASE_URL = "https://api.football-data-api.com/league-matches"

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot está rodando e ativo!"

def buscar_jogos_de_hoje():
    hoje = datetime.now().strftime("%Y-%m-%d")
    encontrados = False
    for league_id in league_ids:
        url = f"{BASE_URL}?key={API_KEY}&league_id={league_id}&date_from={hoje}&date_to={hoje}"
        try:
            response = requests.get(url)
            data = response.json()

            if data.get("success") and data.get("data"):
                for match in data["data"]:
                    time_a = match.get("home_name", "Time A")
                    time_b = match.get("away_name", "Time B")
                    status = match.get("status", "-").upper()
                    minuto = match.get("minute", "-")
                    msg = f"⚽ {time_a} x {time_b}\nStatus: {status} | Minuto: {minuto}"
                    bot.send_message(chat_id=CHAT_ID, text=msg)
                    encontrados = True
            else:
                msg = f"⚠️ Liga {league_id}: Nenhum jogo programado para hoje"
                bot.send_message(chat_id=CHAT_ID, text=msg)
        except Exception as e:
            print(f"Erro ao buscar liga {league_id}: {e}")
            bot.send_message(chat_id=CHAT_ID, text=f"Erro ao buscar jogos da liga {league_id}")

    if not encontrados:
        bot.send_message(chat_id=CHAT_ID, text="📌 Nenhum jogo com data de hoje encontrado nas ligas configuradas.")

if __name__ == "__main__":
    try:
        bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado com sucesso!\n🗓️ Buscando jogos de hoje...")
        buscar_jogos_de_hoje()
    except Exception as e:
        print(f"Erro ao enviar mensagem inicial: {e}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
