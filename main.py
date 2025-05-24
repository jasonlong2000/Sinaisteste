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

ARQUIVO_ENVIADOS = "pre_jogos_footballapi.txt"
ARQUIVO_RESULTADOS = "resultados_pendentes.txt"

bot = Bot(token=BOT_TOKEN)

LIGAS_PERMITIDAS = {
    2, 3, 4, 5, 9, 11, 13, 15, 32, 39, 40, 41, 48, 61, 62,
    66, 71, 72, 73, 75, 78, 79, 135, 140, 141, 143, 145, 307, 477, 484, 541, 556, 742, 866
}

HEADERS = {"x-apisports-key": API_KEY}

def buscar_jogos_do_dia():
    fuso_brasilia = pytz.timezone("America/Sao_Paulo")
    hoje = datetime.now(fuso_brasilia).strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={hoje}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", [])

def buscar_estatisticas(league_id, season, team_id):
    url = f"https://v3.football.api-sports.io/teams/statistics?league={league_id}&season={season}&team={team_id}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", {})

def testar_todos_os_dados():
    jogos = buscar_jogos_do_dia()
    for jogo in jogos:
        league = jogo["league"]
        if league["id"] not in LIGAS_PERMITIDAS:
            continue
        home = jogo["teams"]["home"]
        away = jogo["teams"]["away"]
        stats_home = buscar_estatisticas(league["id"], league["season"], home["id"])
        stats_away = buscar_estatisticas(league["id"], league["season"], away["id"])

        def listar_chaves(stats):
            return "\n".join([f"- {k}" for k in stats.keys()])

        msg_home = f"[HOME] {home['name']}\nChaves disponíveis:\n" + listar_chaves(stats_home)
        msg_away = f"[AWAY] {away['name']}\nChaves disponíveis:\n" + listar_chaves(stats_away)

        bot.send_message(chat_id=CHAT_ID, text=msg_home)
        bot.send_message(chat_id=CHAT_ID, text=msg_away)
        break

if __name__ == "__main__":
    testar_todos_os_dados()
    exit()
