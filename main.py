import os
import requests
from datetime import datetime
from telegram import Bot
from flask import Flask

# Inicialização
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FOOTYSTATS_API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "2012,2015,2023,2030").split(",")  # IDs das ligas

if not BOT_TOKEN or not CHAT_ID or not FOOTYSTATS_API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar configurados.")

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot de jogos do dia ativo."

def get_today_matches():
    hoje = datetime.utcnow().date().isoformat()
    jogos_encontrados = []

    for lid in LEAGUE_IDS:
        url = f"https://api.football-data-api.com/league-matches?key={FOOTYSTATS_API_KEY}&league_id={lid}"
        try:
            response = requests.get(url, timeout=15)
            data = response.json()
            if data.get("success") and "data" in data:
                for jogo in data["data"]:
                    if jogo.get("date", "").startswith(hoje):
                        jogos_encontrados.append(jogo)
        except Exception as e:
            print(f"Erro na liga {lid}: {e}")

    return jogos_encontrados

def formatar_jogo(jogo):
    home = jogo.get("homeTeam", "Time A")
    away = jogo.get("awayTeam", "Time B")
    status = jogo.get("status", "-")
    horario = jogo.get("time", "-")
    return f"\ud83c\udf1f {home} x {away}\nStatus: {status.upper()} | Horário: {horario}"

def main():
    try:
        bot.send_message(chat_id=CHAT_ID, text="\ud83d\ude80 Bot iniciado com sucesso!\n\ud83d\udcc5 Buscando jogos de hoje...")
        partidas = get_today_matches()

        if not partidas:
            bot.send_message(chat_id=CHAT_ID, text="\u26a0\ufe0f Nenhum jogo com data de hoje confirmado.")
        else:
            for jogo in partidas:
                msg = formatar_jogo(jogo)
                bot.send_message(chat_id=CHAT_ID, text=msg)

    except Exception as e:
        print(f"Erro geral: {e}")

if __name__ == "__main__":
    main()
