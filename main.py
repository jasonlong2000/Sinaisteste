import requests
from datetime import datetime
from telegram import Bot

# Configurações
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
CHAT_ID = "-1002675165012"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
SEASON_IDS = [
    13973, 7664, 13965, 13966, 13967, 13968, 13969, 13970, 13971, 13972,
    13974, 13975, 13976, 13977, 13978, 13979, 13980, 13981, 13982, 13983,
    13984, 13985, 13986, 13987, 13988, 13989, 13990, 13991, 13992, 13993,
    13994, 13995, 13996, 13997, 13998, 13999
]

bot = Bot(token=BOT_TOKEN)
enviados = set()


def fetch_matches(season_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&season_id={season_id}"
    try:
        response = requests.get(url)
        return response.json().get("data", [])
    except Exception as e:
        print(f"Erro na API (temporada {season_id}): {e}")
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
    bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado!\n📅 Verificando jogos das ligas configuradas de hoje...")

    novos = 0
    for season_id in SEASON_IDS:
        jogos = fetch_matches(season_id)
        if not jogos:
            continue

        for jogo in jogos:
            jogo_id = jogo.get("id")
            if jogo_id not in enviados:
                texto = formatar_jogo(jogo)
                bot.send_message(chat_id=CHAT_ID, text=texto)
                enviados.add(jogo_id)
                novos += 1

    if novos == 0:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo encontrado hoje nas ligas configuradas.")


if __name__ == "__main__":
    main()
