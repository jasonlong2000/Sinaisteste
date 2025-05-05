# main.py
import os
import requests
from datetime import datetime
from telegram import Bot
from flask import Flask
from threading import Thread
import time

# Configurações via variáveis de ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "").split(",")

# Valida variáveis essenciais
if not BOT_TOKEN or not CHAT_ID or not API_KEY or not LEAGUE_IDS:
    raise RuntimeError("BOT_TOKEN, CHAT_ID, FOOTYSTATS_API_KEY e LEAGUE_IDS precisam estar definidos.")

# Inicializa o bot e Flask
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot ativo!"

def buscar_jogos_de_hoje():
    hoje = datetime.now().strftime("%Y-%m-%d")
    total_jogos = 0
    for lid in LEAGUE_IDS:
        url = f"https://api.football-data-api.com/league-matches?key={API_KEY}&league_id={lid}&date={hoje}"
        try:
            response = requests.get(url)
            data = response.json()
            jogos = data.get("data", [])

            if not jogos:
                bot.send_message(chat_id=CHAT_ID, text=f"⚽ Liga {lid}: Nenhum jogo encontrado para hoje.")
            else:
                total_jogos += len(jogos)
                for jogo in jogos:
                    home = jogo.get("homeTeam", "Time A")
                    away = jogo.get("awayTeam", "Time B")
                    status = jogo.get("status", "-")
                    horario = jogo.get("date", "")
                    msg = f"\U0001F3C0 {home} x {away}\nStatus: {status} | Horário: {horario}"
                    bot.send_message(chat_id=CHAT_ID, text=msg)
        except Exception as e:
            print(f"Erro ao buscar liga {lid}: {e}")

    if total_jogos == 0:
        bot.send_message(chat_id=CHAT_ID, text="\u26a0 Nenhum jogo agendado para hoje nas ligas selecionadas.")
    else:
        bot.send_message(chat_id=CHAT_ID, text=f"\u2705 Total de jogos encontrados: {total_jogos}")

def executar_bot():
    try:
        bot.send_message(chat_id=CHAT_ID, text="\U0001F680 Bot iniciado com sucesso e buscando jogos de hoje...")
        buscar_jogos_de_hoje()
    except Exception as e:
        print(f"Erro ao enviar mensagem inicial: {e}")

if __name__ == "__main__":
    Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": int(os.getenv("PORT", 5000))}).start()
    time.sleep(2)
    executar_bot()
