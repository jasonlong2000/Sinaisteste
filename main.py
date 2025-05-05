import os
import requests
import datetime
from telegram import Bot
from flask import Flask
import threading

# Variáveis de ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FOOTYSTATS_API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "2012,2027,2015,2030")  # Premier League, La Liga, Serie A...

# Verifica variáveis essenciais
if not BOT_TOKEN or not CHAT_ID or not FOOTYSTATS_API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY devem estar definidos.")

# Instancia o bot e servidor
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot ativo!"

def buscar_jogos_hoje():
    hoje = datetime.date.today()
    urls = [
        f"https://api.football-data-api.com/league-matches?key={FOOTYSTATS_API_KEY}&league_id={liga_id}"
        for liga_id in LEAGUE_IDS.split(",")
    ]

    jogos_encontrados = []
    for url in urls:
        try:
            response = requests.get(url)
            data = response.json()
            if not data.get("success"):
                print("Erro na API:", data.get("message"))
                continue

            for jogo in data.get("data", []):
                inicio = jogo.get("date_unix")
                if not inicio:
                    continue
                data_jogo = datetime.datetime.fromtimestamp(inicio).date()
                if data_jogo == hoje:
                    time_a = jogo.get("homeTeam", "Time A")
                    time_b = jogo.get("awayTeam", "Time B")
                    status = jogo.get("status", "-").upper()
                    texto = f"\U0001F3C0 {time_a} x {time_b}\nStatus: {status} | Minuto: -"
                    jogos_encontrados.append(texto)
        except Exception as e:
            print("Erro ao acessar:", url, e)

    return jogos_encontrados

def enviar_jogos():
    try:
        bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado com sucesso!\nBuscando jogos de hoje...")
        jogos = buscar_jogos_hoje()
        if not jogos:
            bot.send_message(chat_id=CHAT_ID, text="⚠ Nenhum jogo com data de hoje confirmado.")
        else:
            for jogo in jogos:
                bot.send_message(chat_id=CHAT_ID, text=jogo)
    except Exception as e:
        print("Erro ao enviar mensagens:", e)

def iniciar():
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    enviar_jogos()

if __name__ == "__main__":
    iniciar()
