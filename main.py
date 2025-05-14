import requests
import json
from datetime import datetime
from telegram import Bot
import pytz
import time
import os

API_KEY = "6810ea1e7c44dab18f4fc039b73e8dd2"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"

ARQUIVO_ENVIADOS = "pre_jogos_footballapi.txt"

bot = Bot(token=BOT_TOKEN)

LIGAS_PERMITIDAS = {
    2, 3, 4, 5, 9, 11, 13, 15, 32, 39, 40, 41, 48, 61, 62,
    66, 71, 72, 73, 75, 78, 79, 135, 140, 143, 145, 477, 484, 541, 556, 742, 866
}

HEADERS = {"x-apisports-key": API_KEY}

def carregar_enviados():
    if os.path.exists(ARQUIVO_ENVIADOS):
        with open(ARQUIVO_ENVIADOS, "r") as f:
            return set(line.strip() for line in f)
    return set()

def salvar_enviado(jogo_id):
    with open(ARQUIVO_ENVIADOS, "a") as f:
        f.write(f"{jogo_id}\n")

def buscar_jogos_do_dia():
    hoje = datetime.now().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={hoje}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", [])

def buscar_estatisticas(league_id, season, team_id):
    url = f"https://v3.football.api-sports.io/teams/statistics?league={league_id}&season={season}&team={team_id}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", {})

def formatar_jogo(jogo):
    fixture = jogo["fixture"]
    league = jogo["league"]
    teams = jogo["teams"]
    home = teams["home"]
    away = teams["away"]

    if league["id"] not in LIGAS_PERMITIDAS:
        return None

    stats_home = buscar_estatisticas(league["id"], league["season"], home["id"])
    stats_away = buscar_estatisticas(league["id"], league["season"], away["id"])

    dt = datetime.utcfromtimestamp(fixture["timestamp"]).astimezone(pytz.timezone("America/Sao_Paulo"))
    data = dt.strftime("%d/%m")
    hora = dt.strftime("%H:%M")

    header = (
        f"⚽ *{home['name']} x {away['name']}*\n"
        f"🌍 {league['name']}\n"
        f"📅 {data} | 🕒 {hora}\n"
        f"📌 Status: {fixture['status']['short']}\n"
    )

    dados_home = json.dumps(stats_home, indent=2, ensure_ascii=False)
    dados_away = json.dumps(stats_away, indent=2, ensure_ascii=False)

    msg = f"{header}\n\n📊 *Estatísticas do Mandante ({home['name']}):*\n```\n{dados_home}\n```\n"
    msg += f"\n📊 *Estatísticas do Visitante ({away['name']}):*\n```\n{dados_away}\n```"

    return msg
def verificar_pre_jogos():
    enviados = carregar_enviados()
    jogos = buscar_jogos_do_dia()

    for jogo in jogos:
        fixture = jogo["fixture"]
        jogo_id = str(fixture["id"])

        if fixture["status"]["short"] != "NS" or jogo_id in enviados:
            continue

        mensagem = formatar_jogo(jogo)

        if mensagem:
            try:
                bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown", disable_web_page_preview=True)
                salvar_enviado(jogo_id)
                time.sleep(3)
            except Exception as e:
                print(f"Erro ao enviar jogo {jogo_id}: {e}")
                time.sleep(5)

    if not jogos:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo encontrado hoje nas ligas selecionadas.", parse_mode="Markdown")

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="✅ Robô ativado! Enviando estatísticas brutas dos jogos do dia...")
    while True:
        verificar_pre_jogos()
        time.sleep(14400)
