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

def sugestao_de_placar(gm1, gm2, gs1, gs2):
    try:
        g1 = round((float(gm1) + float(gs2)) / 2)
        g2 = round((float(gm2) + float(gs1)) / 2)
        alternativa = f"{g1+1} x {g2}" if g1 <= g2 else f"{g1} x {g2+1}"
        return f"{g1} x {g2} ou {alternativa}"
    except:
        return "Indefinido"
def gerar_sugestao(gm_home, gm_away, btts_home, btts_away,
                   clean_home, clean_away, first_goal_home, first_goal_away, shots_home, shots_away,
                   over25_home, over25_away, shots_on_home, shots_on_away,
                   gs_home, gs_away, over15_home, over15_away):
    try:
        gm_home = float(gm_home)
        gm_away = float(gm_away)
        gs_home = float(gs_home)
        gs_away = float(gs_away)
        over15_home = float(over15_home.strip('%'))
        over15_away = float(over15_away.strip('%'))
        under35_home = 3 - float(over25_home.strip('%')) / 100 * 3
        under35_away = 3 - float(over25_away.strip('%')) / 100 * 3
        clean_home = int(clean_home)
        clean_away = int(clean_away)
        fts_home = int(shots_home == "0")
        fts_away = int(shots_away == "0")

        sugestoes = []

        if gm_home >= 1.5 and gs_away >= 1.5 and clean_home >= 1 and fts_away >= 1:
            sugestoes.append("🏆 Vitória provável: Mandante")
        elif gm_away >= 1.5 and gs_home >= 1.5 and clean_away >= 1 and fts_home >= 1:
            sugestoes.append("🏆 Vitória provável: Visitante")

        if (gm_home + gm_away + gs_home + gs_away) >= 6 and over15_home >= 66 and over15_away >= 66:
            sugestoes.append("⚽ Over 1.5 gols")

        if gm_home <= 1.5 and gm_away <= 1.5 and under35_home == 3 and under35_away == 3:
            sugestoes.append("🧤 Under 3.5 gols")

        return "\n".join(sugestoes) if sugestoes else "Sem sugestão clara"
    except:
        return "Sem sugestão clara"

def formatar_jogo(jogo):
    fixture = jogo["fixture"]
    teams = jogo["teams"]
    league = jogo["league"]
    home = teams["home"]
    away = teams["away"]

    stats_home = buscar_estatisticas(league["id"], league["season"], home["id"])
    stats_away = buscar_estatisticas(league["id"], league["season"], away["id"])

    gm_home = formatar_valor(stats_home.get("goals", {}).get("for", {}).get("average", {}).get("total"))
    gm_away = formatar_valor(stats_away.get("goals", {}).get("for", {}).get("average", {}).get("total"))
    gs_home = formatar_valor(stats_home.get("goals", {}).get("against", {}).get("average", {}).get("total"))
    gs_away = formatar_valor(stats_away.get("goals", {}).get("against", {}).get("average", {}).get("total"))
    btts_home = stats_home.get("both_teams_to_score", {}).get("percentage", "0")
    btts_away = stats_away.get("both_teams_to_score", {}).get("percentage", "0")
    clean_home = formatar_valor(stats_home.get("clean_sheet", {}).get("total", "0"))
    clean_away = formatar_valor(stats_away.get("clean_sheet", {}).get("total", "0"))
    first_goal_home = stats_home.get("first_goal", {}).get("for", {}).get("percentage", "0")
    first_goal_away = stats_away.get("first_goal", {}).get("for", {}).get("percentage", "0")
    shots_home = formatar_valor(stats_home.get("shots", {}).get("total", {}).get("average", {}).get("total", "0"))
    shots_away = formatar_valor(stats_away.get("shots", {}).get("total", {}).get("average", {}).get("total", "0"))
    shots_on_home = formatar_valor(stats_home.get("shots", {}).get("on", {}).get("average", {}).get("total", "0"))
    shots_on_away = formatar_valor(stats_away.get("shots", {}).get("on", {}).get("average", {}).get("total", "0"))
    over25_home = stats_home.get("goals", {}).get("average", {}).get("over_25", "0")
    over25_away = stats_away.get("goals", {}).get("average", {}).get("over_25", "0")
    over15_home = stats_home.get("goals", {}).get("average", {}).get("over_15", "0")
    over15_away = stats_away.get("goals", {}).get("average", {}).get("over_15", "0")

    placar = sugestao_de_placar(gm_home, gm_away, gs_home, gs_away)
    sugestoes = gerar_sugestao(gm_home, gm_away, btts_home, btts_away,
                               clean_home, clean_away, first_goal_home, first_goal_away, shots_home, shots_away,
                               over25_home, over25_away, shots_on_home, shots_on_away,
                               gs_home, gs_away, over15_home, over15_away)

    return (
        f"⚽ *{home['name']} x {away['name']}*\n"
        f"🌍 {league['name']}\n"
        f"📅 {datetime.utcfromtimestamp(fixture['timestamp']).astimezone(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m')} | 🕒 {datetime.utcfromtimestamp(fixture['timestamp']).astimezone(pytz.timezone('America/Sao_Paulo')).strftime('%H:%M')}\n"
        f"📌 Status: {fixture['status']['short']}\n\n"
        f"🎯 *Gols esperados:* {home['name']}: {gm_home} | {away['name']}: {gm_away}\n"
        f"❌ *Gols sofridos:* {home['name']}: {gs_home} | {away['name']}: {gs_away}\n"
        f"🔢 *Placar provável:* {placar}\n\n"
        f"💡 *Sugestões de entrada:*\n{sugestoes}"
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
                bot.send_message(chat_id=CHAT_ID, text=mensagem.encode('utf-8').decode('utf-8'), parse_mode="Markdown")
                salvar_enviado(jogo_id)
                novos += 1
                time.sleep(2)
        except Exception as e:
            print(f"Erro ao enviar jogo {jogo_id}: {e}")
            time.sleep(5)

    if novos == 0:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo com dados suficientes hoje.", parse_mode="Markdown")

if __name__ == "__main__":
    while True:
        verificar_pre_jogos()
        time.sleep(21600)
