import requests
import time
import os
import json
from datetime import datetime
from telegram import Bot

API_KEY = os.getenv("API_KEY")
CHAT_ID = os.getenv("CHAT_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")
LEAGUE_ID = "12321"  # ID da Champions League

DISPATCHED_FILE = "sent_matches.json"
bot = Bot(token=BOT_TOKEN)

def carregar_enviados():
    if os.path.exists(DISPATCHED_FILE):
        with open(DISPATCHED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def salvar_enviados(enviados):
    with open(DISPATCHED_FILE, "w") as f:
        json.dump(list(enviados), f)

def fetch_matches():
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={LEAGUE_ID}"
    try:
        r = requests.get(url)
        return r.json().get("data", [])
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return []

def formatar_partida(jogo):
    home = jogo.get("home_name", "Time A")
    away = jogo.get("away_name", "Time B")
    status = jogo.get("status", "-").upper()
    minute = jogo.get("minute", "-")
    liga = jogo.get("league_name", "Liga")
    fase = jogo.get("stage_name", "-")

    horario = "?"
    ts = jogo.get("date_unix")
    if ts:
        horario = datetime.fromtimestamp(ts).strftime("%H:%M")

    return f"⚽ {home} x {away}\nLiga: {liga} | Fase: {fase}\nStatus: {status} | Minuto: {minute} | Horário: {horario}"

def main():
    enviados = carregar_enviados()
    bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado!\n📅 Verificando jogos da Champions League de hoje...")

    novos = 0
    for match in fetch_matches():
        match_id = str(match.get("id"))
        if match_id not in enviados and match.get("status") in ["notstarted", "inplay"]:
            msg = formatar_partida(match)
            try:
                bot.send_message(chat_id=CHAT_ID, text=msg)
                enviados.add(match_id)
                novos += 1
                time.sleep(1.2)
            except Exception as e:
                print(f"Erro ao enviar mensagem: {e}")

    if novos == 0:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo encontrado na Champions League hoje.")
    
    salvar_enviados(enviados)

if __name__ == "__main__":
    main()
