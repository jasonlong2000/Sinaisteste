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

LIGAS_PERMITIDAS = {
    "World - UEFA Champions League",
    "World - CONMEBOL Libertadores",
    "World - CONMEBOL Sudamericana"
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
def formatar_jogo(jogo):
    fixture = jogo["fixture"]
    teams = jogo["teams"]
    league = jogo["league"]
    home = teams["home"]
    away = teams["away"]
    nome_liga = f"{league['country']} - {league['name']}"

    if nome_liga not in LIGAS_PERMITIDAS:
        return None

    try:
        dt = datetime.utcfromtimestamp(fixture["timestamp"]).astimezone(pytz.timezone("America/Sao_Paulo"))
        data = dt.strftime("%d/%m")
        hora = dt.strftime("%H:%M")
    except:
        data, hora = "-", "-"

    stats_home = buscar_estatisticas(league["id"], league["season"], home["id"])
    stats_away = buscar_estatisticas(league["id"], league["season"], away["id"])

    if not stats_home or not stats_away:
        print(f"⚠️ API NÃO RETORNOU ESTATÍSTICAS — HOME: {home['name']} | AWAY: {away['name']}")
        return None

    print(f"\n===== ESTATÍSTICAS DO TIME DA CASA ({home['name']}) =====")
    print(stats_home)
    print(f"\n===== ESTATÍSTICAS DO TIME VISITANTE ({away['name']}) =====")
    print(stats_away)

    return None  # Não envia nada para o Telegram, apenas loga

def verificar_pre_jogos():
    jogos = buscar_jogos_do_dia()

    print(f"Total de jogos encontrados: {len(jogos)}")

    for jogo in jogos:
        fixture = jogo["fixture"]
        jogo_id = str(fixture["id"])
        status = fixture["status"]["short"]

        if status != "NS":
            continue

        try:
            formatar_jogo(jogo)
            time.sleep(2)
        except Exception as e:
            print(f"Erro ao processar jogo {jogo_id}: {e}")
            time.sleep(5)

if __name__ == "__main__":
    while True:
        verificar_pre_jogos()
        time.sleep(21600)  # Executa a cada 6 horas
