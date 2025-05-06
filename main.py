import requests
import time
import os
from telegram import Bot
from datetime import datetime

# Configurações
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"
LEAGUE_ID = 2033  # Champions League
enviados = set()

bot = Bot(token=BOT_TOKEN)

def fetch_matches():
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={LEAGUE_ID}"
    try:
        r = requests.get(url)
        return r.json().get("data", [])
    except Exception as e:
        print("Erro ao buscar jogos:", e)
        return []

def formatar_jogo(jogo):
    home = jogo.get("home_name", "Time A")
    away = jogo.get("away_name", "Time B")
    status = jogo.get("status", "-").upper()
    minuto = jogo.get("minute", "-")
    timestamp = jogo.get("date_unix", 0)
    horario = datetime.fromtimestamp(timestamp).strftime('%H:%M') if timestamp else "?"
    liga = jogo.get("competition_name", "Liga")
    fase = jogo.get("stage", "Fase")
    return f"""
⚽ {home} x {away}
⏱ Status: {status} | Minuto: {minuto}
🕓 Horário: {horario}
🏆 Liga: {liga} - {fase}
""".strip()

def main():
    bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado!\n📅 Verificando jogos da Champions League de hoje...")
    jogos = fetch_matches()

    total = 0
    for jogo in jogos:
        id_jogo = jogo.get("id")
        status = jogo.get("status", "").lower()
        if id_jogo not in enviados and status in ["notstarted", "inplay"]:
            texto = formatar_jogo(jogo)
            bot.send_message(chat_id=CHAT_ID, text=texto)
            enviados.add(id_jogo)
            total += 1
            time.sleep(1.5)

    if total == 0:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo encontrado na Champions League hoje.")

if __name__ == "__main__":
    main()
