import requests
import time
import os
from telegram import Bot
from telegram.error import RetryAfter

# === CONFIGURAÇÕES ===
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
CHAT_ID = os.getenv("CHAT_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Ligas configuradas (IDs conhecidos da API FootyStats)
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
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"[ERRO] Liga {league_id}: {e}")
        return []

def format_match(match):
    home = match.get("home_name", "Time A")
    away = match.get("away_name", "Time B")
    status = match.get("status", "-")
    minute = match.get("minute", "-")
    return f"⚽ {home} x {away}\nStatus: {status.upper()} | Minuto: {minute}"

def send_message_safe(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text)
    except RetryAfter as e:
        print(f"[Aviso] Flood control ativado. Aguardando {e.retry_after} segundos...")
        time.sleep(e.retry_after)
        bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        print(f"[Erro ao enviar mensagem] {e}")

def main():
    send_message_safe("🚀 Bot iniciado!\n📅 Buscando jogos das ligas configuradas...")

    total = 0
    for league_id in LEAGUE_IDS:
        matches = fetch_today_matches(league_id)
        if not matches:
            send_message_safe(f"⚠️ Liga {league_id}: Nenhum jogo encontrado ou erro na API")
        else:
            for match in matches:
                send_message_safe(format_match(match))
                total += 1
        time.sleep(2)

    if total == 0:
        send_message_safe("⚠️ Nenhum jogo agendado para hoje nas ligas selecionadas.")

if __name__ == "__main__":
    main()
