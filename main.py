import os
import requests
import datetime
from telegram import Bot

# Configurações de ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS")  # Ex: "2012,2036,..."

if not BOT_TOKEN or not CHAT_ID or not API_KEY or not LEAGUE_IDS:
    raise RuntimeError("Variáveis de ambiente obrigatórias não definidas.")

bot = Bot(token=BOT_TOKEN)
league_ids = [lid.strip() for lid in LEAGUE_IDS.split(",") if lid.strip()]

BASE_URL = "https://api.football-data-api.com/league-matches"

def get_today_date_str():
    today = datetime.datetime.now().date()
    return today.strftime("%Y-%m-%d")

def fetch_matches_for_league(league_id):
    params = {
        "key": API_KEY,
        "league_id": league_id,
        "date_from": get_today_date_str(),
        "date_to": get_today_date_str(),
        "page": 1
    }
    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"Erro ao buscar dados da liga {league_id}: {e}")
        return []

def enviar_mensagem(texto):
    try:
        bot.send_message(chat_id=CHAT_ID, text=texto)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

def main():
    enviar_mensagem("\ud83d\ude80 Bot iniciado!\n\ud83d\udcc5 Buscando jogos das ligas configuradas...")
    jogos_hoje = 0
    for league_id in league_ids:
        partidas = fetch_matches_for_league(league_id)
        if partidas:
            for match in partidas:
                home = match.get("home_name", "Time A")
                away = match.get("away_name", "Time B")
                status = match.get("status", "unknown").upper()
                msg = f"\ud83c\udf0a {home} x {away}\nStatus: {status}"
                enviar_mensagem(msg)
                jogos_hoje += 1
        else:
            enviar_mensagem(f"\u26a0\ufe0f Liga {league_id}: Nenhum jogo encontrado ou erro na API")

    if jogos_hoje == 0:
        enviar_mensagem("\u26a0\ufe0f Nenhum jogo agendado para hoje nas ligas selecionadas.")

if __name__ == '__main__':
    main()
