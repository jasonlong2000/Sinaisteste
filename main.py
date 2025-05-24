import requests
from datetime import datetime
from telegram import Bot
import pytz
import time
import os

API_KEY = "6810ea1e7c44dab18f4fc039b73e8dd2"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"

bot = Bot(token=BOT_TOKEN)

HEADERS = {"x-apisports-key": API_KEY}


def buscar_jogo_completo():
    hoje = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={hoje}"
    res = requests.get(url, headers=HEADERS).json()
    jogos = res.get("response", [])
    for jogo in jogos:
        return jogo  # pega o primeiro
    return None


def testar_escanteios():
    jogo = buscar_jogo_completo()
    if not jogo:
        bot.send_message(chat_id=CHAT_ID, text="Nenhum jogo encontrado para hoje.")
        return

    fixture_id = jogo["fixture"]["id"]
    home_team = jogo["teams"]["home"]["name"]
    away_team = jogo["teams"]["away"]["name"]

    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
    res = requests.get(url, headers=HEADERS).json()
    stats = res.get("response", [])

    if not stats:
        bot.send_message(chat_id=CHAT_ID, text="Sem estatísticas disponíveis ainda para esse jogo.")
        return

    mensagens = []
    for time_stats in stats:
        team = time_stats["team"]["name"]
        statistics = time_stats["statistics"]
        corners = next((item for item in statistics if item["type"].lower() == "corners" or "corner" in item["type"].lower()), None)
        total = corners["value"] if corners else "N/D"
        mensagens.append(f"{team} teve {total} escanteios")

    bot.send_message(chat_id=CHAT_ID, text="\n".join(mensagens))


if __name__ == "__main__":
    testar_escanteios()
    exit()
