import requests
import time
import os
from telegram import Bot
from datetime import datetime
from flask import Flask
from threading import Thread

API_KEY = os.getenv("FOOTYSTATS_API_KEY")
CHAT_ID = os.getenv("CHAT_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

LEAGUE_IDS = [
    2003, 2004, 2005, 2006, 2007, 2008, 2012, 2013, 2014, 2015, 2016,
    2017, 2022, 2023, 2026, 2031, 2032, 2033, 2034, 2035, 2036, 2037,
    2038, 2039, 2040
]

dispatched_matches = set()
bot = Bot(token=BOT_TOKEN)

def fetch_today_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        response = requests.get(url)
        return response.json().get("data", [])
    except Exception as e:
        print(f"Erro na liga {league_id}: {e}")
        return []

def format_match(match):
    home = match.get("home_name", "Time A")
    away = match.get("away_name", "Time B")
    status = match.get("status", "-").upper()
    minute = match.get("minute", "-")
    timestamp = match.get("date_unix", 0)
    horario = datetime.fromtimestamp(timestamp).strftime('%d/%m %H:%M') if timestamp else "?"
    return f"⚽ {home} x {away}\nStatus: {status} | Minuto: {minute} | Horário: {horario}"

def verificar_jogos():
    total = 0
    for league_id in LEAGUE_IDS:
        matches = fetch_today_matches(league_id)
        if not matches:
            continue
        for match in matches:
            match_id = match.get("id")
            status = match.get("status", "").lower()
            if match_id not in dispatched_matches and status in ["notstarted", "inplay"]:
                text = format_match(match)
                bot.send_message(chat_id=CHAT_ID, text=text)
                dispatched_matches.add(match_id)
                total += 1
                time.sleep(1.5)
    if total == 0:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo encontrado agora.")

def main_loop():
    bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado!\n🔁 Atualizando a cada 6 horas...")
    while True:
        verificar_jogos()
        time.sleep(21600)  # 6 horas = 21600 segundos

# === Servidor Flask para manter ativo no Render ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot está rodando!"

if __name__ == "__main__":
    Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": int(os.environ.get("PORT", 5000))}, daemon=True).start()
    main_loop()
