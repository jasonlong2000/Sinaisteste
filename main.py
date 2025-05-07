import requests
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
HEADERS = {"x-apisports-key": API_KEY}

LIGAS_PERMITIDAS = {
    "World - UEFA Champions League",
    "World - CONMEBOL Libertadores",
    "World - CONMEBOL Sudamericana"
}

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
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        return res.json().get("response", [])
    except:
        return []

def buscar_estatisticas(league_id, season, team_id):
    url = f"https://v3.football.api-sports.io/teams/statistics?league={league_id}&season={season}&team={team_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.json().get("response", {})
    except:
        return {}

def formatar_estatisticas(stats, nome):
    if not stats:
        return f"*{nome}*: estatísticas indisponíveis"

    gols = stats['goals']
    btts = stats.get('both_teams_to_score', {}).get('total', '-')
    clean_sheet = stats.get('clean_sheet', {}).get('total', '-')
    posse = stats.get('ball_possession', '-')
    chutes = stats.get('shots', {}).get('total', {}).get('total', '-')
    no_gol = stats.get('shots', {}).get('on', {}).get('total', '-')
    faltas = stats.get('fouls', {}).get('total', '-')
    passes = stats.get('passes', {}).get('accuracy', '-')
    escanteios = stats.get('corners', {}).get('total', {}).get('total', '-')
    amarelos = stats.get('cards', {}).get('yellow', {}).get('total', '-')
    vermelhos = stats.get('cards', {}).get('red', {}).get('total', '-')

    return (
        f"- Gols: {gols['for']['total']['total']} marcados | {gols['against']['total']['total']} sofridos\n"
        f"- Posse: {posse}% | Chutes: {chutes} (no gol: {no_gol})\n"
        f"- Faltas: {faltas} | Passes certos: {passes}%\n"
        f"- Escanteios: {escanteios} | Cartões: {amarelos} amarelos, {vermelhos} vermelhos\n"
        f"- BTTS: {btts} jogos | Clean sheets: {clean_sheet}"
    )

def formatar_jogo(jogo):
    fixture = jogo["fixture"]
    teams = jogo["teams"]
    league = jogo["league"]
    home = teams["home"]
    away = teams["away"]
    nome_liga = f"{league['country']} - {league['name']}"

    if nome_liga not in LIGAS_PERMITIDAS:
        return None

    dt = datetime.utcfromtimestamp(fixture["timestamp"]).astimezone(pytz.timezone("America/Sao_Paulo"))
    data = dt.strftime("%d/%m")
    hora = dt.strftime("%H:%M")

    stats_home = buscar_estatisticas(league["id"], league["season"], home["id"])
    stats_away = buscar_estatisticas(league["id"], league["season"], away["id"])

    estats_home = formatar_estatisticas(stats_home, home["name"])
    estats_away = formatar_estatisticas(stats_away, away["name"])

    return (
        f"⚽ *{home['name']} x {away['name']}*\n"
        f"🌍 {league['name']} | 📅 {data} 🕒 {hora}\n"
        f"📌 Status: {fixture['status']['short']}\n\n"
        f"📊 *Estatísticas por time:*\n\n"
        f"🏠 *{home['name']}*\n{estats_home}\n\n"
        f"🏃 *{away['name']}*\n{estats_away}"
    )

def verificar_pre_jogos():
    enviados = carregar_enviados()
    jogos = buscar_jogos_do_dia()

    for jogo in jogos:
        fixture = jogo["fixture"]
        jogo_id = str(fixture["id"])
        status = fixture["status"]["short"]

        if status != "NS" or jogo_id in enviados:
            continue

        mensagem = formatar_jogo(jogo)
        if mensagem:
            bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
            salvar_enviado(jogo_id)
            time.sleep(2)

if __name__ == "__main__":
    while True:
        verificar_pre_jogos()
        time.sleep(21600)  # a cada 6 horas
