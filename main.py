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

def gerar_sugestao(gm_home, gm_away, btts_home, btts_away,
                   clean_home, clean_away, first_goal_home, first_goal_away,
                   gs_home, gs_away, over15_home, over15_away, over25_home, over25_away,
                   minutos_home, minutos_away):
    try:
        gm_home = float(gm_home)
        gm_away = float(gm_away)
        gs_home = float(gs_home)
        gs_away = float(gs_away)
        over15_home = float(over15_home.strip('%'))
        over15_away = float(over15_away.strip('%'))
        over25_home = float(over25_home.strip('%'))
        over25_away = float(over25_away.strip('%'))
        btts_home = float(btts_home.strip('%'))
        btts_away = float(btts_away.strip('%'))
        fg_home = float(first_goal_home.strip('%'))
        clean_home = int(clean_home)
        clean_away = int(clean_away)

        alta_conf = []
        media_conf = []
        soma_ataque = gm_home + gm_away
        soma_defesa = gs_home + gs_away
        btts_media = (btts_home + btts_away) / 2

        # Dupla Chance — apenas a de maior probabilidade
        diff = gm_home - gm_away
        if diff >= 0.2 and gs_away >= 1.1:
            if gm_home >= 1.3:
                alta_conf.append("🔐 Dupla chance: 1X (alta)")
            elif gm_home >= 1.1:
                media_conf.append("🔐 Dupla chance: 1X (média)")
        elif diff <= -0.2 and gs_home >= 1.1:
            if gm_away >= 1.3:
                alta_conf.append("🔐 Dupla chance: X2 (alta)")
            elif gm_away >= 1.1:
                media_conf.append("🔐 Dupla chance: X2 (média)")

        # Over 1.5 — novos critérios
        if soma_ataque >= 2.5 and soma_defesa >= 1.5:
            alta_conf.append("⚽ Over 1.5 gols (alta)")
        elif soma_ataque >= 2.0 and soma_defesa >= 1.0:
            media_conf.append("⚠️ Over 1.5 gols (média)")

        return "\n".join(alta_conf + media_conf) if alta_conf or media_conf else "Sem sugestão clara"

    except:
        return "Sem sugestão clara"
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
    over25_home = stats_home.get("goals", {}).get("average", {}).get("over_25", "0")
    over25_away = stats_away.get("goals", {}).get("average", {}).get("over_25", "0")
    over15_home = stats_home.get("goals", {}).get("average", {}).get("over_15", "0")
    over15_away = stats_away.get("goals", {}).get("average", {}).get("over_15", "0")
    minutos_home = stats_home.get("goals", {}).get("for", {}).get("minute", {})
    minutos_away = stats_away.get("goals", {}).get("against", {}).get("minute", {})

    placar = sugestao_de_placar(gm_home, gm_away, gs_home, gs_away)
    sugestoes = gerar_sugestao(gm_home, gm_away, btts_home, btts_away,
                               clean_home, clean_away, first_goal_home, first_goal_away,
                               gs_home, gs_away, over15_home, over15_away,
                               over25_home, over25_away, minutos_home, minutos_away)

    salvar_resultado_previsto(fixture["id"], home["name"], away["name"], sugestoes.replace("\n", " | "))

    dt = datetime.utcfromtimestamp(fixture["timestamp"]).astimezone(pytz.timezone("America/Sao_Paulo"))
    data = dt.strftime("%d/%m")
    hora = dt.strftime("%H:%M")

    return (
        f"⚽ *{home['name']} x {away['name']}*\n"
        f"🌍 {league['name']}\n"
        f"📅 {data} | 🕒 {hora}\n"
        f"📌 Status: {fixture['status']['short']}\n\n"
        f"🔢 *Placar provável:* {placar}\n\n"
        f"💡 *Sugestões:*\n{sugestoes}"
    )

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
            bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
            salvar_enviado(jogo_id)
            time.sleep(2)

def verificar_resultados():
    if not os.path.exists(ARQUIVO_RESULTADOS):
        return
    with open(ARQUIVO_RESULTADOS, "r") as f:
        linhas = f.readlines()

    alto_total = alto_green = 0
    medio_total = medio_green = 0

    for linha in linhas:
        jogo_id, time_home, time_away, previsao = linha.strip().split(";")
        url = f"https://v3.football.api-sports.io/fixtures?id={jogo_id}"
        res = requests.get(url, headers=HEADERS).json()
        if not res["response"]:
            continue
        jogo = res["response"][0]
        if jogo["fixture"]["status"]["short"] != "FT":
            continue

        gols_home = jogo["goals"]["home"]
        gols_away = jogo["goals"]["away"]
        entradas = previsao.split(" | ")
        resultado = []

        for entrada in entradas:
            tipo = "alto" if "(alta" in entrada else "medio"
            acertou = False
            if "Over 1.5" in entrada and (gols_home + gols_away) >= 2:
                acertou = True
            if "Under 3.5" in entrada and (gols_home + gols_away) <= 3:
                acertou = True
            if "Dupla chance: 1X" in entrada and gols_home >= gols_away:
                acertou = True
            if "Dupla chance: X2" in entrada and gols_away >= gols_home:
                acertou = True
            if "Ambas Marcam" in entrada and gols_home > 0 and gols_away > 0:
                acertou = True
            if "Over 2.5" in entrada and (gols_home + gols_away) > 2:
                acertou = True
            if "Gol no 1º tempo" in entrada and (gols_home + gols_away) > 0:
                acertou = True

            if tipo == "alto":
                alto_total += 1
                if acertou: alto_green += 1
            elif tipo == "medio":
                medio_total += 1
                if acertou: medio_green += 1

            resultado.append(f"{'✅' if acertou else '❌'} {entrada}")

        resumo = (
            f"📊 *{time_home} x {time_away}* terminou {gols_home} x {gols_away}\n"
            f"🎯 Previsões:\n" + "\n".join(resultado)
        )
        bot.send_message(chat_id=CHAT_ID, text=resumo, parse_mode="Markdown")

    final = f"📈 *Resumo final:*\n"
    final += f"⭐ Risco alto: {alto_green}/{alto_total} green\n" if alto_total else ""
    final += f"⚠️ Risco médio: {medio_green}/{medio_total} green" if medio_total else ""
    bot.send_message(chat_id=CHAT_ID, text=final, parse_mode="Markdown")

if __name__ == "__main__":
    while True:
        verificar_pre_jogos()
        verificar_resultados()
        time.sleep(14400)
