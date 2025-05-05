import os
import requests
import datetime
from telegram import Bot
from flask import Flask
from threading import Thread

# Configurações via variáveis de ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FOOTYSTATS_API_KEY = os.getenv("FOOTYSTATS_API_KEY")

# API correta para jogos de hoje
API_URL = f"https://api.football-data-api.com/todays-matches?key={FOOTYSTATS_API_KEY}"

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot está ativo e rodando!"

def enviar_mensagem(texto):
    try:
        bot.send_message(chat_id=CHAT_ID, text=texto)
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

def buscar_jogos_hoje():
    hoje = datetime.datetime.utcnow().date()
    try:
        response = requests.get(API_URL)
        data = response.json()
        jogos = data.get("data", [])

        if not jogos:
            enviar_mensagem("⚠️ Nenhum jogo encontrado para hoje na API.")
            return

        encontrados = 0
        for jogo in jogos:
            status = jogo.get("status", "").lower()
            data_jogo = jogo.get("date_start", "")
            if not data_jogo:
                continue

            try:
                data_convertida = datetime.datetime.strptime(data_jogo, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                continue

            if data_convertida == hoje:
                encontrados += 1
                home = jogo.get("home_name", "Time A")
                away = jogo.get("away_name", "Time B")
                msg = f"\U0001F3DF *Jogo de Hoje*\n{home} x {away}\nStatus: {status.upper()}\nData: {data_jogo}"
                enviar_mensagem(msg)

        if encontrados == 0:
            enviar_mensagem("⚠️ Nenhum jogo com data de hoje confirmado.")

    except Exception as e:
        print("Erro ao buscar jogos:", e)
        enviar_mensagem("Erro ao buscar jogos de hoje.")

def iniciar():
    enviar_mensagem("🚀 Bot iniciado com sucesso! Buscando jogos de hoje...")
    buscar_jogos_hoje()

if __name__ == "__main__":
    Thread(target=iniciar).start()
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta)
