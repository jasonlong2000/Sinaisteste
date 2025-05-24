import requests
from datetime import datetime
from telegram import Bot
import pytz
import time
import os
import json

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
        return jogo
    return None


def listar_todas_chaves():
    jogo = buscar_jogo_completo()
    if not jogo:
        bot.send_message(chat_id=CHAT_ID, text="Nenhum jogo encontrado para hoje.")
        return

    league = jogo["league"]
    home = jogo["teams"]["home"]
    away = jogo["teams"]["away"]
    stats_home = buscar_estatisticas(league["id"], league["season"], home["id"])
    stats_away = buscar_estatisticas(league["id"], league["season"], away["id"])

    def chaves(stats):
        return "\n".join([f"- {k}" for k in stats.keys()])

    bot.send_message(chat_id=CHAT_ID, text=f"[HOME] {home['name']}\nChaves disponíveis:\n{chaves(stats_home)}")
    bot.send_message(chat_id=CHAT_ID, text=f"[AWAY] {away['name']}\nChaves disponíveis:\n{chaves(stats_away)}")


def buscar_estatisticas(league_id, season, team_id):
    url = f"https://v3.football.api-sports.io/teams/statistics?league={league_id}&season={season}&team={team_id}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", {})


if __name__ == "__main__":
    listar_todas_chaves()
    exit()
