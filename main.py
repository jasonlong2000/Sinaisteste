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
        clean_home = int(stats_home["clean_sheet"]["total"])
        clean_away = int(stats_away["clean_sheet"]["total"])
        shots_on_home = float(stats_home.get("shots", {}).get("on", {}).get("average", {}).get("total", 0))
        shots_on_away = float(stats_away.get("shots", {}).get("on", {}).get("average", {}).get("total", 0))

        wins_home = stats_home.get("fixtures", {}).get("wins", {}).get("home", 0)
        wins_away = stats_away.get("fixtures", {}).get("wins", {}).get("away", 0)
        gols_home_casa = float(stats_home["goals"]["for"]["average"].get("home", 0))
        gols_away_fora = float(stats_away["goals"]["for"]["average"].get("away", 0))
        sofre_home_casa = float(stats_home["goals"]["against"]["average"].get("home", 0))
        sofre_away_fora = float(stats_away["goals"]["against"]["average"].get("away", 0))

        alta_conf = []
        media_conf = []

        # Under 3.5
        if gm_home + gm_away <= 2.4 and gs_home + gs_away <= 2.0 and (shots_on_home + shots_on_away) < 6:
            alta_conf.append("🧤 Under 3.5 gols (alta)")
        elif gm_home + gm_away <= 2.8 and gs_home + gs_away <= 2.2 and (shots_on_home + shots_on_away) < 8:
            media_conf.append("🧤 Under 3.5 gols (média)")

        # Dupla Chance
        if wins_home >= 3 and gols_home_casa >= 1.5 and sofre_home_casa < 1.0 and sofre_away_fora >= 1.5:
            alta_conf.append("🔐 Dupla chance: 1X (alta)")
        elif wins_home >= 2 and gols_home_casa >= 1.2 and sofre_home_casa <= 1.3 and sofre_away_fora >= 1.3:
            media_conf.append("🔐 Dupla chance: 1X (média)")
        if wins_away >= 3 and gols_away_fora >= 1.5 and sofre_away_fora < 1.0 and sofre_home_casa >= 1.5:
            alta_conf.append("🔐 Dupla chance: X2 (alta)")
        elif wins_away >= 2 and gols_away_fora >= 1.2 and sofre_away_fora <= 1.3 and sofre_home_casa >= 1.3:
            media_conf.append("🔐 Dupla chance: X2 (média)")

        # Over 1.5
        soma_gols = gm_home + gm_away
        soma_sofridos = gs_home + gs_away
        total_clean = clean_home + clean_away
        if soma_gols >= 2.5 and soma_sofridos >= 2.0 and total_clean <= 5:
            alta_conf.append("⚽ Over 1.5 gols (alta)")
        elif soma_gols >= 2.0 and soma_sofridos >= 2.0 and total_clean <= 6:
            media_conf.append("⚠️ Over 1.5 gols (média)")

        debug = (
            f"(Debug: gm={gm_home+gm_away}, gs={gs_home+gs_away}, "
            f"clean={clean_home+clean_away}, shots={shots_on_home+shots_on_away})"
        )

        todas = alta_conf + media_conf
        return "\n".join(todas + [debug]) if todas else "Sem sugestão clara\n" + debug
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
    bot.send_message(chat_id=CHAT_ID, text="🔍 Verificando resultados de jogos anteriores...")
    if not os.path.exists(ARQUIVO_RESULTADOS):
        bot.send_message(chat_id=CHAT_ID, text="📁 Nenhum arquivo de resultados encontrado.")
        return

    with open(ARQUIVO_RESULTADOS, "r") as f:
        linhas = f.readlines()

    alto_total = alto_green = 0
    medio_total = medio_green = 0
    resultados_encontrados = 0

    for linha in linhas:
        jogo_id, time_home, time_away, previsao = linha.strip().split(";")
        url = f"https://v3.football.api-sports.io/fixtures?id={jogo_id}"
        res = requests.get(url, headers=HEADERS).json()
        if not res["response"]:
            continue
        jogo = res["response"][0]
        if jogo["fixture"]["status"]["short"] != "FT":
            continue

        resultados_encontrados += 1
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

            if tipo == "alto":
                alto_total += 1
                if acertou:
                    alto_green += 1
            elif tipo == "medio":
                medio_total += 1
                if acertou:
                    medio_green += 1

            resultado.append(f"{'✅' if acertou else '❌'} {entrada}")

        resumo = (
            f"📊 *{time_home} x {time_away}* terminou {gols_home} x {gols_away}\n"
            f"🎯 Previsões:\n" + "\n".join(resultado)
        )
        bot.send_message(chat_id=CHAT_ID, text=resumo, parse_mode="Markdown")

    if resultados_encontrados == 0:
        bot.send_message(chat_id=CHAT_ID, text="ℹ️ Nenhum jogo finalizado ainda.")

    final = f"📈 *Resumo final:*\n"
    final += f"⭐ Risco alto: {alto_green}/{alto_total} green\n" if alto_total else ""
    final += f"⚠️ Risco médio: {medio_green}/{medio_total} green" if medio_total else ""
    bot.send_message(chat_id=CHAT_ID, text=final.strip(), parse_mode="Markdown")

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="✅ Robô ativado com Under 3.5, Dupla Chance e Over 1.5!")
    while True:
        verificar_pre_jogos()
        verificar_resultados()
        time.sleep(14400)
