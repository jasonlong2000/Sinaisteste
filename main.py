import os
import threading
import requests
import schedule
import time
from flask import Flask
from telegram import Bot
from datetime import datetime

# Configurações
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FOOTYSTATS_API_KEY = os.getenv("FOOTYSTATS_API_KEY")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
FOOTYSTATS_URL = f"https://api.football-data-api.com/fixtures?key={FOOTYSTATS_API_KEY}"

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot de análise pré-jogo está ativo."

def enviar_mensagem(texto):
    try:
        requests.post(TELEGRAM_URL, data={"chat_id": CHAT_ID, "text": texto})
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

def analisar_pre_jogos():
    enviar_mensagem("✅ Bot de análise pré-jogo iniciado!")
    try:
        resp = requests.get(FOOTYSTATS_URL)
        data = resp.json().get("data", [])

        hoje = datetime.now().date()
        for jogo in data:
            data_jogo = jogo.get("date_unix")
            if not data_jogo:
                continue
            data_jogo = datetime.fromtimestamp(data_jogo)
            if data_jogo.date() != hoje:
                continue

            home = jogo.get("home_name", "Time A")
            away = jogo.get("away_name", "Time B")
            hora = data_jogo.strftime("%H:%M")

            # Over 1.5
            over15 = jogo.get("over_1_5", 0)
            over_percent = int(over15 * 100) if over15 else 0

            # Escanteios
            avg_corners = jogo.get("avg_corners_total", 0)

            # Cartões
            yellow = jogo.get("avg_yellow_cards", 0)
            red = jogo.get("avg_red_cards", 0)
            total_cartoes = round(yellow + red, 1)

            texto = f"\n📊 *Pré-jogo: {home} x {away}* ({hora})"
            texto += f"\n✅ Over 1.5 em {over_percent}% dos jogos"
            texto += f"\n✅ Média de escanteios: {avg_corners}"
            texto += f"\n🟨 Média de cartões: {total_cartoes}"

            enviar_mensagem(texto)

    except Exception as e:
        print("Erro ao buscar ou processar dados:", e)

def loop_agendado():
    schedule.every().day.at("08:00").do(analisar_pre_jogos)
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    threading.Thread(target=loop_agendado, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
