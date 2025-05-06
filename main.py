import requests
from datetime import datetime
from telegram import Bot

# Configurações
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
CHAT_ID = "-1002675165012"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
LEAGUE_ID = 12321  # Champions League

bot = Bot(token=BOT_TOKEN)
enviados = set()

def fetch_matches():
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={LEAGUE_ID}"
    try:
        response = requests.get(url)
        return response.json().get("data", [])
    except Exception as e:
        print(f"Erro na API: {e}")
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

    return f"⚽ {home} x {away}\nLiga: {liga} | Fase: {fase}\nStatus: {status} | Minuto: {minuto} | Horário: {horario}"

def main():
    bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado! Verificando jogos da Champions League de hoje...")
    jogos = fetch_matches()

    if not jogos:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo encontrado na Champions League hoje.")
        return

    novos = 0
    for jogo in jogos:
        jogo_id = jogo.get("id")
        if jogo_id not in enviados:
            texto = formatar_jogo(jogo)
            bot.send_message(chat_id=CHAT_ID, text=texto)
            enviados.add(jogo_id)
            novos += 1

    if novos == 0:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo encontrado agora.")

if __name__ == "__main__":
    main()
