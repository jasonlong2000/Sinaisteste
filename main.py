import requests
from telegram import Bot

API_KEY = "6810ea1e7c44dab18f4fc039b73e8dd2"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"

HEADERS = {"x-apisports-key": API_KEY}
URL = "https://v3.football.api-sports.io/leagues"

def listar_ligas():
    res = requests.get(URL, headers=HEADERS)
    ligas = res.json()["response"]

    texto = "📋 *Lista de Ligas disponíveis na API:*\n\n"
    count = 0

    for liga in ligas:
        nome = liga["league"]["name"]
        id_liga = liga["league"]["id"]
        pais = liga["country"]["name"]
        texto += f"ID: {id_liga} | {nome} ({pais})\n"
        count += 1
        if count >= 40:
            break  # evita mensagem muito longa

    bot = Bot(token=BOT_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")

if __name__ == "__main__":
    listar_ligas()
