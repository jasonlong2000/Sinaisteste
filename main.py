import os
import requests
from datetime import datetime
from telegram import Bot

# === CONFIGURAÇÕES ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")

# Teste com Premier League (ID: 2012)
LEAGUE_ID = "2012"
API_URL = f"https://api.football-data-api.com/league-matches?key={API_KEY}&league_id={LEAGUE_ID}"

def enviar_mensagem(texto):
    try:
        bot = Bot(token=BOT_TOKEN)
        bot.send_message(chat_id=CHAT_ID, text=texto)
        print("Mensagem enviada com sucesso.")
    except Exception as e:
        print("Erro ao enviar:", e)

def buscar_jogos_hoje():
    try:
        response = requests.get(API_URL)
        data = response.json()

        if not data.get("success"):
            enviar_mensagem("Erro da API: " + data.get("message", "Sem mensagem"))
            return

        jogos = data.get("data", [])
        hoje = datetime.now().date().isoformat()

        encontrados = 0
        for jogo in jogos:
            status = jogo.get("status", "")
            data_jogo = jogo.get("date", "").split(" ")[0]

            if data_jogo == hoje:
                encontrados += 1
                msg = f"⚽ {jogo['homeTeam']} x {jogo['awayTeam']}\nStatus: {status}\nData: {jogo['date']}"
                enviar_mensagem(msg)

        if encontrados == 0:
            enviar_mensagem("⚠️ Nenhum jogo encontrado hoje na Premier League.")

    except Exception as e:
        enviar_mensagem("Erro ao buscar jogos: " + str(e))

# === EXECUÇÃO ===
if __name__ == "__main__":
    enviar_mensagem("🚀 Teste iniciado. Buscando jogos da Premier League (ID 2012)...")
    buscar_jogos_hoje()
