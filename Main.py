import asyncio
import requests
import time
from flask import Flask
import threading
from telegram import Bot

# === CONFIGURAÇÕES ===
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
API_URL = f"https://api.football-data-api.com/todays-matches?key={API_KEY}"

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ativo no Render!"

def manter_online():
    app.run(host="0.0.0.0", port=10000)

async def send_message(text):
    await asyncio.to_thread(bot.send_message, chat_id=CHAT_ID, text=text, parse_mode="Markdown")

async def verificar_sinais():
    await send_message("✅ Bot ativado e monitorando jogos com 4 estratégias.")

    sinais_enviados = set()
    while True:
        try:
            res = await asyncio.to_thread(requests.get, API_URL, timeout=10)
            dados = res.json()
            agora = time.time()

            for jogo in dados.get("data", []):
                id = jogo.get("id")
                if not id or jogo.get("status") == "complete":
                    continue

                tempo = int((agora - jogo.get("date_unix", 0)) / 60)
                chutes = (jogo.get("team_a_shotsOnTarget", 0) + jogo.get("team_b_shotsOnTarget", 0))
                corners = (jogo.get("team_a_corners", 0) + jogo.get("team_b_corners", 0))
                posse = max(jogo.get("team_a_possession", 0), jogo.get("team_b_possession", 0))
                faltas = jogo.get("team_a_fouls", 0) + jogo.get("team_b_fouls", 0)
                placar = jogo.get("score", "0-0")

                # Estratégia 1: Over 0.5 HT
                if 25 <= tempo <= 45 and chutes >= 6 and corners >= 4 and posse >= 60:
                    chave = f"{id}_ht"
                    if chave not in sinais_enviados:
                        await send_message(f"⚽ *Over 0.5 HT com pressão!*\nJogo: {jogo['home_name']} x {jogo['away_name']}\nMinuto: {tempo}'\nChutes: {chutes}, Escanteios: {corners}, Posse: {posse}%")
                        sinais_enviados.add(chave)

                # Estratégia 2: Over 1.5 FT
                if 50 <= tempo <= 75 and placar == "0-0" and chutes >= 12 and corners >= 5:
                    chave = f"{id}_ft"
                    if chave not in sinais_enviados:
                        await send_message(f"🔥 *Over 1.5 FT com pressão!*\nJogo: {jogo['home_name']} x {jogo['away_name']}\nMinuto: {tempo}'\nChutes: {chutes}, Escanteios: {corners}")
                        sinais_enviados.add(chave)

                # Estratégia 3: Cartões
                if tempo <= 80 and faltas >= 20 and chutes >= 10 and corners >= 8:
                    chave = f"{id}_cartao"
                    if chave not in sinais_enviados:
                        await send_message(f"🟨 *Cartão provável!*\nJogo: {jogo['home_name']} x {jogo['away_name']}\nMinuto: {tempo}'\nFaltas: {faltas}, Chutes: {chutes}, Escanteios: {corners}")
                        sinais_enviados.add(chave)

                # Estratégia 4: Escanteios prováveis
                if 10 <= tempo <= 75 and posse >= 60 and chutes >= 10 and corners <= 6:
                    chave = f"{id}_escanteio"
                    if chave not in sinais_enviados:
                        await send_message(f"🚩 *Escanteio esperado!*\nJogo: {jogo['home_name']} x {jogo['away_name']}\nMinuto: {tempo}'\nChutes: {chutes}, Escanteios: {corners}, Posse: {posse}%")
                        sinais_enviados.add(chave)

        except Exception as e:
            print("Erro:", e)

        await asyncio.sleep(120)

# Iniciar Flask + Loop do Bot
if __name__ == "__main__":
    threading.Thread(target=manter_online).start()
    asyncio.run(verificar_sinais())
