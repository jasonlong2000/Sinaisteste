import requests
from datetime import datetime
from telegram import Bot

# Configurações
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
CHAT_ID = "-1002675165012"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"

LEAGUE_IDS = [
    2003, 2004, 2005, 2006, 2007, 2008, 2012, 2013, 2014, 2015, 2016,
    2017, 2022, 2023, 2026, 2031, 2032, 2033, 2034, 2035, 2036, 2037,
    2038, 2039, 2040, 12321  # Champions League incluída
]

bot = Bot(token=BOT_TOKEN)
enviados = set()

def fetch_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        response = requests.get(url)
        return response.json().get("data", [])
    except Exception as e:
        print(f"Erro ao buscar liga {league_id}: {e}")
        return []

def formatar_jogo(jogo):
    home = jogo.get("home_name", "Time A")
    away = jogo.get("away_name", "Time B")
    status = jogo.get("status", "-").upper()
    minuto = jogo.get("minute", "-")
    liga = jogo.get("league_name", "Liga")
    fase = jogo.get("stage_name", "-")
    timestamp = jogo.get("date_unix", 0)
    horario = datetime.fromtimestamp(timestamp).strftime('%H:%M') if timestamp else "?"
    data = datetime.fromtimestamp(timestamp).strftime('%d/%m') if timestamp else "?"
    
    return f"⚽ {home} x {away}\nLiga: {liga} | Fase: {fase}\nStatus: {status} | Minuto: {minuto}\nHorário: {horario} | Data: {data}"

def main():
    bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado! Verificando jogos das ligas de hoje...")
    total_novos = 0

    for league_id in LEAGUE_IDS:
        jogos = fetch_matches(league_id)
        if not jogos:
            bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Liga {league_id}: Nenhum jogo encontrado ou erro na API.")
            continue

        for jogo in jogos:
            jogo_id = jogo.get("id")
            if jogo_id not in enviados:
                texto = formatar_jogo(jogo)
                bot.send_message(chat_id=CHAT_ID, text=texto)
                enviados.add(jogo_id)
                total_novos += 1

    if total_novos == 0:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo encontrado hoje nas ligas configuradas.")

if __name__ == "__main__":
    main()
