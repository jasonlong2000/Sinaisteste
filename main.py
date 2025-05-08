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

def formatar_valor(v):
    return str(v) if v not in [None, "-", ""] else "0"

def gerar_sugestoes(stats_home, stats_away):
    sugestoes = []

    try:
        gm_home = float(stats_home["goals"]["for"]["average"]["total"])
        gm_away = float(stats_away["goals"]["for"]["average"]["total"])
        gs_home = float(stats_home["goals"]["against"]["average"]["total"])
        gs_away = float(stats_away["goals"]["against"]["average"]["total"])

        over15_home = stats_home["goals"]["for"]["under_over"]["1.5"]["over"]
        over15_away = stats_away["goals"]["for"]["under_over"]["1.5"]["over"]
        under35_home = stats_home["goals"]["for"]["under_over"]["3.5"]["under"]
        under35_away = stats_away["goals"]["for"]["under_over"]["3.5"]["under"]

        jogos_home = stats_home["fixtures"]["played"]["total"]
        jogos_away = stats_away["fixtures"]["played"]["total"]

        clean_home = stats_home["clean_sheet"]["total"]
        clean_away = stats_away["clean_sheet"]["total"]
        fts_home = stats_home["failed_to_score"]["total"]
        fts_away = stats_away["failed_to_score"]["total"]

        # VitÃ³ria provÃ¡vel
        if gm_home >= 1.5 and gs_away >= 1.5 and clean_home >= 1 and fts_away >= 1:
            sugestoes.append("ð VitÃ³ria provÃ¡vel: Mandante")
        elif gm_away >= 1.5 and gs_home >= 1.5 and clean_away >= 1 and fts_home >= 1:
            sugestoes.append("ð VitÃ³ria provÃ¡vel: Visitante")

        # Over 1.5
        if (gm_home + gm_away + gs_home + gs_away) >= 6 and over15_home >= 2 and over15_away >= 2:
            sugestoes.append("â½ Over 1.5 gols")

        # Under 3.5
        if gm_home <= 1.5 and gm_away <= 1.5 and under35_home == jogos_home and under35_away == jogos_away:
            sugestoes.append("ð§¤ Under 3.5 gols")

        return "\n".join(sugestoes) if sugestoes else "Sem sugestÃ£o clara"
    except:
        return "Erro ao gerar sugestÃ£o"

def formatar_jogo(jogo):
    fixture = jogo["fixture"]
    teams = jogo["teams"]
    league = jogo["league"]
    home = teams["home"]
    away = teams["away"]

    stats_home = buscar_estatisticas(league["id"], league["season"], home["id"])
    stats_away = buscar_estatisticas(league["id"], league["season"], away["id"])

    if not stats_home or not stats_away:
        print(f"â ï¸ Dados ausentes: {home['name']} x {away['name']}")
        return None

    dt = datetime.utcfromtimestamp(fixture["timestamp"]).astimezone(pytz.timezone("America/Sao_Paulo"))
    data = dt.strftime("%d/%m")
    hora = dt.strftime("%H:%M")

    sugestoes = gerar_sugestoes(stats_home, stats_away)

    return (
        f"â½ *{home['name']} x {away['name']}*\n"
        f"ð {league['name']}\n"
        f"ð {data} | ð {hora}\n"
        f"ð Status: {fixture['status']['short']}\n\n"
        f"ð¡ *SugestÃµes de entrada:*\n{sugestoes}"
    )

def verificar_pre_jogos():
    enviados = carregar_enviados()
    jogos = buscar_jogos_do_dia()
    novos = 0

    for jogo in jogos:
        fixture = jogo["fixture"]
        jogo_id = str(fixture["id"])
        status = fixture["status"]["short"]

        if status != "NS" or jogo_id in enviados:
            continue

        try:
            mensagem = formatar_jogo(jogo)
            if mensagem:
                bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
                salvar_enviado(jogo_id)
                novos += 1
                time.sleep(2)
        except Exception as e:
            print(f"Erro ao enviar jogo {jogo_id}: {e}")
            time.sleep(5)

    if novos == 0:
        bot.send_message(chat_id=CHAT_ID, text="â ï¸ Nenhum jogo novo com dados suficientes hoje.", parse_mode="Markdown")

if __name__ == "__main__":
    while True:
        verificar_pre_jogos()
        time.sleep(21600)
