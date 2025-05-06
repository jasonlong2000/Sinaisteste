import requests
import time
import os
from telegram import Bot
from datetime import datetime

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
    horario = datetime.fromtimestamp(timestamp).strftime('%H:%M') if timestamp else "?"
    data = datetime.fromtimestamp(timestamp).strftime('%d/%m') if timestamp else "?"
    league = match.get("league_name", "?")
    stage = match.get("stage", "?")
    return f"\u26bd {home} x {away}\nLiga: {league} | Fase: {stage}\nStatus: {status} | Minuto: {minute} | Hor\u00e1rio: {horario} | Data: {data}"

def main():
    bot.send_message(chat_id=CHAT_ID, text="\ud83d\ude80 Bot iniciado!\n\ud83d\udcc5 Atualizando a cada 6 horas...")
    total = 0

    for league_id in LEAGUE_IDS:
        matches = fetch_today_matches(league_id)

        if not matches:
            msg = f"\u26a0\ufe0f Liga {league_id}: Nenhum jogo encontrado ou erro na API"
            bot.send_message(chat_id=CHAT_ID, text=msg)
            continue

        for match in matches:
            match_id = match.get("id")
            status = match.get("status", "").lower()
            if match_id not in dispatched_matches and status in ["notstarted", "inplay"]:
                text = format_match(match)
                bot.send_message(chat_id=CHAT_ID, text=text)
                dispatched_matches.add(match_id)
                total += 1
                time.sleep(1.5)  # evitar flood

    if total == 0:
        bot.send_message(chat_id=CHAT_ID, text="\u26a0\ufe0f Nenhum jogo ativo ou programado para hoje nas ligas selecionadas.")

if __name__ == "__main__":
    main()
