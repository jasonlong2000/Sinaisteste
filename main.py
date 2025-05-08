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
LIGAS_PERMITIDAS = {13, 14, 2}

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

def verificar_pre_jogos():
    enviados = carregar_enviados()
    jogos = buscar_jogos_do_dia()

    for jogo in jogos:
        fixture = jogo["fixture"]
        teams = jogo["teams"]
        league = jogo["league"]
        home = teams["home"]
        away = teams["away"]

        if league["id"] not in LIGAS_PERMITIDAS:
            continue

        jogo_id = str(fixture["id"])
        if fixture["status"]["short"] != "NS" or jogo_id in enviados:
            continue

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

        salvar_enviado(jogo_id)
        salvar_resultado_previsto(jogo_id, home["name"], away["name"], sugestoes.replace("\n", " | "))

        mensagem = (
            f"⚽ *{home['name']} x {away['name']}*\n"
            f"🌍 {league['name']}\n"
            f"📅 {datetime.utcfromtimestamp(fixture['timestamp']).astimezone(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m')} "
            f"| 🕒 {datetime.utcfromtimestamp(fixture['timestamp']).astimezone(pytz.timezone('America/Sao_Paulo')).strftime('%H:%M')}\n\n"
            f"💡 *Sugestões:*\n{sugestoes}"
        )

        bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
        time.sleep(2)

def verificar_resultados():
    if not os.path.exists(ARQUIVO_RESULTADOS):
        return

    with open(ARQUIVO_RESULTADOS, "r") as f:
        linhas = f.readlines()

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
        acertos = []

        if "Over 1.5" in previsao and (gols_home + gols_away) >= 2:
            acertos.append("✅ Over 1.5")
        if "Under 3.5" in previsao and (gols_home + gols_away) <= 3:
            acertos.append("✅ Under 3.5")
        if "Vitória provável: Mandante" in previsao and gols_home > gols_away:
            acertos.append("✅ Mandante venceu")
        if "Vitória provável: Visitante" in previsao and gols_away > gols_home:
            acertos.append("✅ Visitante venceu")

        texto = (
            f"📊 *{time_home} x {time_away}* terminou {gols_home} x {gols_away}\n"
            f"🎯 Previsões: {previsao}\n"
            f"📌 Resultado: {' | '.join(acertos) if acertos else '❌ Nenhum palpite confirmado'}"
        )

        bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")

if __name__ == "__main__":
    while True:
        verificar_pre_jogos()
        verificar_resultados()
        time.sleep(14400)  # 4 horas
