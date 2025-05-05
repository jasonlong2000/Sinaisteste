import requests
import time
from telegram import Bot

API_KEY = "SUA_API_KEY"
CHAT_ID = "-1002675165012"
BOT_TOKEN = "SEU_BOT_TOKEN"

LEAGUE_IDS = [
    2003, 2004, 2005, 2006, 2007, 2008,
    2012, 2013, 2014, 2015, 2016, 2017,
    2022, 2023, 2026, 2031, 2032, 2033,
    2034, 2035, 2036, 2037, 2038, 2039,
    2040
]

bot = Bot(token=BOT_TOKEN)

def fetch_today_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        response = requests.get(url, timeout=10)
        return response.json().get("data", [])
    except Exception as e:
        print(f"Erro ao buscar liga {league_id}: {e}")
        return []

def format_match(match):
    home = match.get("home_name", "Time A")
    away = match.get("away_name", "Time B")
    status = match.get("status", "-")
    minute = match.get("minute", "-")
    return f"\u26BD {home} x {away}\nStatus: {status.upper()} | Minuto: {minute}"

def buscar_jogos():
    bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado!\n📅 Buscando jogos do dia...")
    total = 0
    for lid in LEAGUE_IDS:
        matches = fetch_today_matches(lid)
        if not matches:
            bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Liga {lid}: Nenhum jogo encontrado ou erro.")
        else:
            for m in matches:
                msg = format_match(m)
                try:
                    bot.send_message(chat_id=CHAT_ID, text=msg)
                    time.sleep(1.5)
                    total += 1
                except Exception as e:
                    print(f"Erro ao enviar: {e}")
    if total == 0:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo confirmado para hoje nas ligas configuradas.")

if __name__ == "__main__":
    while True:
        buscar_jogos()
        time.sleep(21600)  # espera 6h
