import os
import requests
from datetime import datetime
from telegram import Bot

# Configurações
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "12137,14231,14210,14305,13857,13939,13863,12325,12036,12451,12473,9816,12446,12321,12327,12053,12278,12337,2426,12529,11084,1410,9128,13734,13878,12076,11500,12530,12316,13624,12535,13973").split(",")

bot = Bot(token=BOT_TOKEN)

def fetch_today_matches(league_id):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"https://api.football-data-api.com/league-matches?key={API_KEY}&league_id={league_id}&date_from={today}&date_to={today}"
    try:
        response = requests.get(url, timeout=10)
        return response.json().get("data", [])
    except Exception as e:
        print(f"Erro ao buscar dados da liga {league_id}: {e}")
        return []

def format_match(match):
    home = match.get("home_name", "Time A")
    away = match.get("away_name", "Time B")
    status = match.get("status", "-")
    minute = match.get("minute", "-")
    return f"\ud83c\udf1f {home} x {away}\nStatus: {status.upper()} | Minuto: {minute}"

def main():
    bot.send_message(chat_id=CHAT_ID, text="\ud83d\ude80 Bot iniciado!\n\ud83d\udcc5 Buscando jogos das ligas configuradas...")
    total_matches = 0
    for league_id in LEAGUE_IDS:
        matches = fetch_today_matches(league_id)
        if not matches:
            bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Liga {league_id}: Nenhum jogo encontrado ou erro na API")
        else:
            for match in matches:
                msg = format_match(match)
                bot.send_message(chat_id=CHAT_ID, text=msg)
                total_matches += 1
    if total_matches == 0:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo agendado para hoje nas ligas selecionadas.")

if __name__ == "__main__":
    main()
