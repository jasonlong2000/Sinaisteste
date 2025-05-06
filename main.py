import requests
import time
import os
import threading
from telegram import Bot
from datetime import datetime
import schedule

# === CONFIGURAÇÕES ===
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"

LEAGUE_IDS = [
    2003, 2004, 2005, 2006, 2007, 2008, 2012, 2013, 2014, 2015, 2016,
    2017, 2022, 2023, 2026, 2031, 2032, 2033, 2034, 2035, 2036, 2037,
    2038, 2039, 2040
]

bot = Bot(token=BOT_TOKEN)
dispatched = set()


def fetch_today_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        res = requests.get(url)
        return res.json().get("data", [])
    except Exception as e:
        print(f"Erro ao buscar liga {league_id}: {e}")
        return []


def format_match(match):
    home = match.get("home_name", "Time A")
    away = match.get("away_name", "Time B")
    status = match.get("status", "-").upper()
    minute = match.get("minute", "-")
    date = datetime.fromtimestamp(match.get("date_unix", 0)).strftime('%d/%m %H:%M')
    league = match.get("competition_name", "Liga desconhecida")
    stage = match.get("competition_stage_name", "Fase não informada")

    return (
        f"⚽ {home} x {away}\n"
        f"Status: {status} | Minuto: {minute} | Data: {date}\n"
        f"Liga: {league} | Fase: {stage}"
    )


def enviar_alertas():
    bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado!\n📅 Buscando jogos do dia...")

    total = 0
    for league_id in LEAGUE_IDS:
        partidas = fetch_today_matches(league_id)
        if not partidas:
            bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Liga {league_id}: Nenhum jogo encontrado ou erro na API.")
            continue

        for jogo in partidas:
            id_jogo = jogo.get("id")
            status = jogo.get("status", "").lower()

            if id_jogo not in dispatched and status in ["notstarted", "inplay"]:
                mensagem = format_match(jogo)
                bot.send_message(chat_id=CHAT_ID, text=mensagem)
                dispatched.add(id_jogo)
                total += 1
                time.sleep(1.5)  # evita flood

    if total == 0:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo ativo ou programado para hoje nas ligas selecionadas.")


def agendar_loop():
    schedule.every(6).hours.do(enviar_alertas)
    enviar_alertas()  # primeira execução imediata

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    thread = threading.Thread(target=agendar_loop)
    thread.start()
