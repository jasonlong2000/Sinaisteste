# main.py
import os
import requests
from datetime import datetime
from telegram import Bot
from flask import Flask
from threading import Thread

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FOOTYSTATS_API_KEY = os.getenv("FOOTYSTATS_API_KEY")

# Lista de ligas específicas para buscar
LEAGUE_IDS = [
    "2022", "2027", "2015", "2030", "2016", "2031", "2013", "2032", "2014", "2033",
    "2038", "2023", "2036", "2034", "2035", "2037", "2040", "2012", "2039", "2060",
    "2061", "2062", "2063", "2041", "2050", "2042", "2043", "2044", "2045", "2046",
    "2047", "2048", "2049", "2051", "2052", "2053", "2054", "2055", "2056", "2057",
    "2058", "2059", "2064", "2065", "2066", "2067", "2068", "2069", "2070"
]

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

@app.route("/")
def home():
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
        bot.send_message(chat_id=CHAT_ID, text="\ud83d\ude80 Bot iniciado!\n\ud83d\udcc5 Buscando jogos das ligas configuradas...")
        partidas = get_today_matches()

        if not partidas:
            bot.send_message(chat_id=CHAT_ID, text="\u26a0\ufe0f Nenhum jogo agendado para hoje nas ligas selecionadas.")
        else:
            for jogo in partidas:
                msg = formatar_jogo(jogo)
                bot.send_message(chat_id=CHAT_ID, text=msg)

    except Exception as e:
        print(f"Erro geral: {e}")

if __name__ == "__main__":
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    main()
