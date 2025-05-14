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
        shots_on_home = float(stats_home["shots"]["on"]["average"]["total"])
        shots_on_away = float(stats_away["shots"]["on"]["average"]["total"])
        goals_home_home = float(stats_home["goals"]["for"]["average"]["home"])
        goals_away_away = float(stats_away["goals"]["for"]["average"]["away"])
        goals_home_against_home = float(stats_home["goals"]["against"]["average"]["home"])
        goals_away_against_away = float(stats_away["goals"]["against"]["average"]["away"])
        wins_home_home = stats_home["fixtures"]["wins"]["home"]
        wins_away_away = stats_away["fixtures"]["wins"]["away"]

        alta_conf = []

        # Dupla Chance 1X
        if (
            wins_home_home > 3
            and goals_home_home > 1.5
            and goals_home_against_home < 1.0
            and goals_away_against_away > 1.5
        ):
            alta_conf.append("🔐 Dupla chance: 1X (alta)")

        # Dupla Chance X2
        if (
            wins_away_away > 3
            and goals_away_away > 1.5
            and goals_away_against_away < 1.0
            and goals_home_against_home > 1.5
        ):
            alta_conf.append("🔐 Dupla chance: X2 (alta)")

        # Under 1.5 Mandante
        if goals_home_home <= 1.0 and goals_away_against_away < 1.0:
            alta_conf.append("❌ Under 1.5 mandante (alta)")

        # Under 1.5 Visitante
        if goals_home_against_home < 1.0 and goals_away_away <= 1.0:
            alta_conf.append("❌ Under 1.5 visitante (alta)")

        # Under 3.5 (jogo)
        if gs_home + gs_away < 2.5 and gm_home + gm_away < 2.0:
            alta_conf.append("🧤 Under 3.5 gols (alta)")

        # Over 7.5 chutes no alvo
        if shots_on_home + shots_on_away > 10 and gm_home + gm_away > 2.0:
            alta_conf.append("🎯 Over 7.5 chutes no alvo (alta)")

        return "\n".join(alta_conf) if alta_conf else "Sem sugestão clara"
    except:
        return "Sem sugestão clara"

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

    total = green = 0

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
            acertou = False
            if "Dupla chance: 1X" in entrada and gols_home >= gols_away:
                acertou = True
            if "Dupla chance: X2" in entrada and gols_away >= gols_home:
                acertou = True
            if "Under 1.5 mandante" in entrada and gols_home <= 1:
                acertou = True
            if "Under 1.5 visitante" in entrada and gols_away <= 1:
                acertou = True
            if "Under 3.5" in entrada and (gols_home + gols_away) <= 3:
                acertou = True
            if "chutes no alvo" in entrada and (gols_home + gols_away) > 2:
                acertou = True

            total += 1
            if acertou:
                green += 1

            resultado.append(f"{'✅' if acertou else '❌'} {entrada}")

        resumo = (
            f"📊 *{time_home} x {time_away}* terminou {gols_home} x {gols_away}\n"
            f"🎯 Previsões:\n" + "\n".join(resultado)
        )
        bot.send_message(chat_id=CHAT_ID, text=resumo, parse_mode="Markdown")

    final = f"📈 *Resumo final:*\n{green}/{total} green"
    bot.send_message(chat_id=CHAT_ID, text=final, parse_mode="Markdown")

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="✅ Robô de previsões ativado com sucesso!")
    while True:
        verificar_pre_jogos()
        verificar_resultados()
        time.sleep(14400)
