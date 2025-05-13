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
ARQUIVO_RESULTADOS = "resultados_pendentes.txt"

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

def salvar_resultado_previsto(jogo_id, time_home, time_away, previsao):
    with open(ARQUIVO_RESULTADOS, "a") as f:
        f.write(f"{jogo_id};{time_home};{time_away};{previsao}\n")

def buscar_jogos_do_dia():
    hoje = datetime.now().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={hoje}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", [])

def buscar_estatisticas(league_id, season, team_id):
    url = f"https://v3.football.api-sports.io/teams/statistics?league={league_id}&season={season}&team={team_id}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", {})

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

def formatar_jogo(jogo):
    fixture = jogo["fixture"]
    teams = jogo["teams"]
    league = jogo["league"]
    home = teams["home"]
    away = teams["away"]

    if league["id"] not in LIGAS_PERMITIDAS:
        return None

    stats_home = buscar_estatisticas(league["id"], league["season"], home["id"])
    stats_away = buscar_estatisticas(league["id"], league["season"], away["id"])

    placar = sugestao_de_placar(
        stats_home["goals"]["for"]["average"]["total"],
        stats_away["goals"]["for"]["average"]["total"],
        stats_home["goals"]["against"]["average"]["total"],
        stats_away["goals"]["against"]["average"]["total"]
    )

    sugestoes = gerar_sugestao(stats_home, stats_away)

    salvar_resultado_previsto(
        fixture["id"], home["name"], away["name"],
        sugestoes.replace("\n", " | ") if sugestoes else "Sem sugestão clara"
    )

    dt = datetime.utcfromtimestamp(fixture["timestamp"]).astimezone(pytz.timezone("America/Sao_Paulo"))
    data = dt.strftime("%d/%m")
    hora = dt.strftime("%H:%M")

    return (
        f"⚽ *{home['name']} x {away['name']}*\n"
        f"🌍 {league['name']}\n"
        f"📅 {data} | 🕒 {hora}\n"
        f"📌 Status: {fixture['status']['short']}\n\n"
        f"🔢 *Placar provável:* {placar}\n\n"
        f"💡 *Sugestões:*\n{sugestoes if sugestoes else 'Sem sugestão clara'}"
    )
def gerar_sugestao(stats_home, stats_away):
    try:
        gm_home = float(stats_home["goals"]["for"]["average"]["total"])
        gm_away = float(stats_away["goals"]["for"]["average"]["total"])
        gs_home = float(stats_home["goals"]["against"]["average"]["total"])
        gs_away = float(stats_away["goals"]["against"]["average"]["total"])
        over25_home = float(stats_home["goals"]["average"]["over_25"])
        over25_away = float(stats_away["goals"]["average"]["over_25"])
        btts_home = float(stats_home["both_teams_to_score"]["percentage"].strip('%'))
        btts_away = float(stats_away["both_teams_to_score"]["percentage"].strip('%'))
        clean_home = int(stats_home["clean_sheet"]["total"])
        clean_away = int(stats_away["clean_sheet"]["total"])
        fg_home = float(stats_home["first_goal"]["for"]["percentage"].strip('%'))
        fg_away = float(stats_away["first_goal"]["for"]["percentage"].strip('%'))
        shots_on_home = float(stats_home["shots"]["on"]["average"]["total"])
        shots_on_away = float(stats_away["shots"]["on"]["average"]["total"])
        goals_home_home = float(stats_home["goals"]["for"]["average"]["home"])
        goals_away_away = float(stats_away["goals"]["for"]["average"]["away"])
        goals_home_against_home = float(stats_home["goals"]["against"]["average"]["home"])
        goals_away_against_away = float(stats_away["goals"]["against"]["average"]["away"])
        form_home = stats_home.get("form", "")
        form_away = stats_away.get("form", "")

        alta_conf = []
        media_conf = []

        # Dupla Chance
        derrotas_casa = form_home.count("L")
        derrotas_fora = form_away.count("L")
        if (derrotas_casa <= 1 or derrotas_fora >= 3) and gm_home >= 1.3 and gs_away >= 1.3 and fg_home >= 60:
            alta_conf.append("🔐 Dupla chance: 1X (alta)")
        elif derrotas_casa < 2:
            media_conf.append("🔐 Dupla chance: 1X (média)")
        if (derrotas_fora <= 1 or derrotas_casa >= 3) and gm_away >= 1.3 and gs_home >= 1.3 and fg_away >= 60:
            alta_conf.append("🔐 Dupla chance: X2 (alta)")
        elif derrotas_fora < 2:
            media_conf.append("🔐 Dupla chance: X2 (média)")

        # Gol no 1º tempo
        faixas = ["0-15", "16-30", "31-45"]
        gols_ht_home = sum(1 for faixa in faixas if stats_home["goals"]["for"]["minute"].get(faixa, {}).get("total"))
        gols_ht_away = sum(1 for faixa in faixas if stats_away["goals"]["against"]["minute"].get(faixa, {}).get("total"))
        if gols_ht_home >= 2 and gols_ht_away >= 2 and fg_home >= 60:
            alta_conf.append("⏱️ Gol no 1º tempo (alta)")
        elif gols_ht_home >= 1 and gols_ht_away >= 1 and fg_home >= 50:
            media_conf.append("⏱️ Gol no 1º tempo (média)")

        # Under 3.5
        if gm_home <= 1.0 and gm_away <= 1.0 and clean_home + clean_away >= 6 and shots_on_home + shots_on_away < 7 and btts_home + btts_away < 120:
            alta_conf.append("🧤 Under 3.5 gols (alta)")
        elif gm_home <= 1.3 and gm_away <= 1.3 and clean_home + clean_away >= 4 and shots_on_home + shots_on_away < 8 and btts_home + btts_away < 130:
            media_conf.append("🧤 Under 3.5 gols (média)")

        # Over 0.5 Mandante
        if gm_home >= 2.0 and gs_away >= 1.5 and shots_on_home > 4 and fg_home >= 60:
            alta_conf.append("⚽ Gol do mandante (alta)")
        elif gm_home >= 1.5 and gs_away >= 1.0 and shots_on_home > 4 and fg_home >= 60:
            media_conf.append("⚠️ Gol do mandante (média)")

        # Over 0.5 Visitante
        if gm_away >= 2.0 and gs_home >= 1.5 and shots_on_away > 4 and fg_away >= 60:
            alta_conf.append("⚽ Gol do visitante (alta)")
        elif gm_away >= 1.5 and gs_home >= 1.0 and shots_on_away > 4 and fg_away >= 60:
            media_conf.append("⚠️ Gol do visitante (média)")

        # Under 1.5 por local
        if goals_away_away < 1.0 and goals_home_against_home < 1.0:
            alta_conf.append("❌ Under 1.5 visitante (alta)")
        elif goals_away_away <= 1.2 and goals_home_against_home <= 1.2:
            media_conf.append("❌ Under 1.5 visitante (média)")
        if goals_home_home < 1.0 and goals_away_against_away < 1.0:
            alta_conf.append("❌ Under 1.5 mandante (alta)")
        elif goals_home_home <= 1.2 and goals_away_against_away <= 1.2:
            media_conf.append("❌ Under 1.5 mandante (média)")

        # Over 7.5 chutes ao gol
        if shots_on_home + shots_on_away >= 10 and gm_home + gm_away >= 2.5:
            alta_conf.append("🎯 Over 7.5 chutes no alvo (alta)")
        elif shots_on_home + shots_on_away >= 8 and gm_home + gm_away >= 2.0:
            media_conf.append("🎯 Over 7.5 chutes no alvo (média)")

        return "\n".join(alta_conf + media_conf) if alta_conf or media_conf else "Sem sugestão clara"
    except:
        return "Sem sugestão clara"

# EXECUÇÃO
if __name__ == "__main__":
    while True:
        verificar_pre_jogos()
        verificar_resultados()
        time.sleep(14400)
