# main.py
import os
import requests
from datetime import datetime
from telegram import Bot
from flask import Flask
from threading import Thread

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "").split(",")

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

@app.route("/")
def home():
    return "Bot online e funcionando!"

def buscar_jogos_hoje():
    hoje = datetime.now().strftime("%Y-%m-%d")
    headers = {"accept": "application/json"}

    for lid in LEAGUE_IDS:
        lid = lid.strip()
        url = f"https://api.football-data-api.com/league-matches?key={API_KEY}&league_id={lid}"
        try:
            response = requests.get(url, headers=headers)
            data = response.json()

            if data.get("success") and data.get("data"):
                jogos = [j for j in data["data"] if j.get("date") == hoje]
                if not jogos:
                    bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Liga {lid}: Nenhum jogo programado para hoje")
                    continue
                for jogo in jogos:
                    home = jogo.get("homeTeam", "Time A")
                    away = jogo.get("awayTeam", "Time B")
                    hora = jogo.get("time", "-")
                    status = jogo.get("status", "-")
                    msg = f"\u26bd {home} x {away}\nStatus: {status} | Horário: {hora}"
                    bot.send_message(chat_id=CHAT_ID, text=msg)
            else:
                bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Liga {lid}: Nenhum jogo encontrado ou erro na API")
        except Exception as e:
            print(f"Erro ao buscar dados da liga {lid}: {e}")
            bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Erro ao buscar dados da liga {lid}.")

def iniciar_bot():
    bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado com sucesso!\nBuscando jogos de hoje...")
    buscar_jogos_hoje()

if __name__ == "__main__":
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))).start()
    iniciar_bot()
