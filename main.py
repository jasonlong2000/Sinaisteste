import os
import requests
import datetime
from telegram import Bot
from flask import Flask
from threading import Thread

# === CONFIGURAÇÕES ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "").split(",")

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

@app.route("/")
def home():
    return "Bot online."

def enviar_mensagem(texto):
    try:
        bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="HTML")
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

def buscar_jogos_do_dia():
    hoje = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).date()  # Horário de Brasília
    encontrou = False

    for league_id in LEAGUE_IDS:
        url = f"https://api.football-data-api.com/league-matches?key={API_KEY}&league_id={league_id}"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            jogos = data.get("data", [])
        except Exception as e:
            print(f"Erro na API da liga {league_id}: {e}")
            continue

        for jogo in jogos:
            try:
                timestamp = jogo.get("date_start")
                if not timestamp:
                    continue
                data_jogo = datetime.datetime.fromtimestamp(timestamp, datetime.timezone(datetime.timedelta(hours=-3))).date()
                if data_jogo == hoje:
                    home = jogo.get("home_name", "Time A")
                    away = jogo.get("away_name", "Time B")
                    horario = datetime.datetime.fromtimestamp(timestamp, datetime.timezone(datetime.timedelta(hours=-3))).strftime("%H:%M")
                    status = jogo.get("status", "-").upper()
                    msg = f"
