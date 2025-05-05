import os
import requests
from datetime import datetime
from telegram import Bot
from flask import Flask

# Configurações
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")

# Validação
if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY devem estar configurados.")

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot ativo."

def buscar_jogos_hoje():
    hoje = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.football-data-api.com/matches?key={API_KEY}&date_from={hoje}&date_to={hoje}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("success") and data.get("data"):
            jogos = data["data"]
            jogos_hoje = [j for j in jogos if j.get("status") in ["not_started", "incomplete"]]
            if not jogos_hoje:
                bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo agendado para hoje encontrado.")
                return

            bot.send_message(chat_id=CHAT_ID, text=f"\ud83c\udf1f {len(jogos_hoje)} jogo(s) encontrados para hoje!")
            for jogo in jogos_hoje:
                casa = jogo.get("home_name", "Time A")
                fora = jogo.get("away_name", "Time B")
                horario = jogo.get("date") or "horário indefinido"
                msg = f"\ud83c\udf1f {casa} x {fora}\nStatus: {jogo.get('status', '-')}, Horário: {horario}"
                bot.send_message(chat_id=CHAT_ID, text=msg)
        else:
            bot.send_message(chat_id=CHAT_ID, text="⚠️ Erro ao buscar jogos do dia.")
    except Exception as e:
        bot.send_message(chat_id=CHAT_ID, text=f"❌ Erro ao consultar a API: {e}")

if __name__ == "__main__":
    buscar_jogos_hoje()
