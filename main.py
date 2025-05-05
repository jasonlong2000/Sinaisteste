import requests
import time
from telegram import Bot

# === Configurações ===
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
CHAT_ID = "-1002675165012"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"

# IDs atualizados de ligas
LEAGUE_IDS = [
    2003, 2004, 2005, 2006, 2007, 2008, 2012, 2013, 2014, 2015, 2016, 2017,
    2022, 2023, 2026, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039,
    2040, 2041, 2042, 2043, 2044, 2045, 2046, 2047, 2048
]

bot = Bot(token=BOT_TOKEN)


def fetch_today_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"Erro ao buscar dados da liga {league_id}: {e}")
        return []


def format_match(match):
    home = match.get("home_name", "Time A")
    away = match.get("away_name", "Time B")
    status = match.get("status", "-")
    minute = match.get("minute", "-")
    return f"⚽ {home} x {away}\nStatus: {status.upper()} | Minuto: {minute}"


def main():
    bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado!\n🗓️ Buscando jogos das ligas configuradas...")

    total_matches = 0
    for league_id in LEAGUE_IDS:
        matches = fetch_today_matches(league_id)
        if not matches:
            msg = f"⚠️ Liga {league_id}: Nenhum jogo encontrado ou erro na API"
            bot.send_message(chat_id=CHAT_ID, text=msg)
        else:
            for match in matches:
                formatted = format_match(match)
                bot.send_message(chat_id=CHAT_ID, text=formatted)
                time.sleep(1)  # Reduz risco de Flood
                total_matches += 1
        time.sleep(2)  # pausa entre ligas

    if total_matches == 0:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo agendado para hoje nas ligas selecionadas.")


if __name__ == "__main__":
    main()
