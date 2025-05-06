import requests
import time
from datetime import datetime
from telegram import Bot
from telegram.error import RetryAfter

# Configurações
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
CHAT_ID = "-1002675165012"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
LEAGUE_IDS = [
    12321,  # Champions League
    2003, 2004, 2005, 2006, 2007, 2008, 2012, 2013, 2014, 2015, 2016,
    2017, 2022, 2023, 2026, 2031, 2032, 2033, 2034, 2035, 2036, 2037,
    2038, 2039, 2040
]

bot = Bot(token=BOT_TOKEN)
enviados = set()

def enviar_msg(texto):
    while True:
        try:
            bot.send_message(chat_id=CHAT_ID, text=texto)
            break
        except RetryAfter as e:
            print(f"Flood control: esperando {e.retry_after} segundos")
            time.sleep(e.retry_after + 1)

def fetch_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        response = requests.get(url)
        return response.json().get("data", [])
    except Exception as e:
        print(f"Erro na API (liga {league_id}): {e}")
        return []

def formatar_jogo(jogo):
    home = jogo.get("home_name", "Time A")
    away = jogo.get("away_name", "Time B")
    status = jogo.get("status", "-").upper()
    minuto = jogo.get("minute", "-")
    liga = jogo.get("league_name", "Liga")
    fase = jogo.get("stage_name", "-")
    timestamp = jogo.get("date_unix", 0)
    horario = datetime.fromtimestamp(timestamp).strftime('%d/%m %H:%M') if timestamp else "?"
    return f"\u26bd {home} x {away}\nLiga: {liga} | Fase: {fase}\nStatus: {status} | Minuto: {minuto} | Horário: {horario}"

def main():
    enviar_msg("\ud83d\ude80 Bot iniciado!\n\ud83d\udd52 Atualizando a cada 6 horas...")
    novos = 0

    for league_id in LEAGUE_IDS:
        jogos = fetch_matches(league_id)
        if not jogos:
            enviar_msg(f"\u26a0\ufe0f Liga {league_id}: Nenhum jogo encontrado ou erro na API")
            continue

        for jogo in jogos:
            jogo_id = jogo.get("id")
            status = jogo.get("status", "").lower()
            if jogo_id not in enviados and status in ["notstarted", "inplay"]:
                texto = formatar_jogo(jogo)
                enviar_msg(texto)
                enviados.add(jogo_id)
                novos += 1
                time.sleep(1.5)

    if novos == 0:
        enviar_msg("\u26a0\ufe0f Nenhum jogo novo encontrado agora.")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(6 * 3600)  # 6 horas
