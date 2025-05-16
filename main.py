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
    66, 71, 72, 73, 75, 78, 79, 135, 140, 141, 143, 145, 307, 477, 484, 541, 556, 742, 866
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
    fuso_brasilia = pytz.timezone("America/Sao_Paulo")
    hoje_br = datetime.now(fuso_brasilia).strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={hoje_br}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", [])

def buscar_estatisticas(league_id, season, team_id):
    url = f"https://v3.football.api-sports.io/teams/statistics?league={league_id}&season={season}&team={team_id}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", {})

def gerar_sugestao(stats_home, stats_away):
    try:
        gm_home = float(stats_home["goals"]["for"]["average"]["total"])
        gm_away = float(stats_away["goals"]["for"]["average"]["total"])
        gs_home = float(stats_home["goals"]["against"]["average"]["total"])
        gs_away = float(stats_away["goals"]["against"]["average"]["total"])
        shots_home = float(stats_home.get("shots", {}).get("on", {}).get("average", {}).get("total", 0))
        shots_away = float(stats_away.get("shots", {}).get("on", {}).get("average", {}).get("total", 0))
        clean_home = int(stats_home.get("clean_sheet", {}).get("total", 0))
        clean_away = int(stats_away.get("clean_sheet", {}).get("total", 0))

        form_home = stats_home.get("form", "")
        form_away = stats_away.get("form", "")

        gols_home_casa = float(stats_home["goals"]["for"]["average"].get("home", 0))
        gols_away_fora = float(stats_away["goals"]["for"]["average"].get("away", 0))
        sofre_home_casa = float(stats_home["goals"]["against"]["average"].get("home", 0))
        sofre_away_fora = float(stats_away["goals"]["against"]["average"].get("away", 0))

        alta_conf = []
        media_conf = []

        # Estratégias aqui continuam na Parte 2
        # Under 3.5
        if gm_home + gm_away <= 2.4 and gs_home + gs_away <= 2.0 and (shots_home + shots_away) < 6:
            alta_conf.append("🧤 Under 3.5 gols (alta)")
        elif gm_home + gm_away <= 2.8 and gs_home + gs_away <= 2.2 and (shots_home + shots_away) < 8:
            media_conf.append("🧤 Under 3.5 gols (média)")

        # Dupla Chance
        L_home = form_home.count("L")
        L_away = form_away.count("L")
        if L_home < 3 and gols_home_casa >= 1.2 and sofre_home_casa <= 1.3 and sofre_away_fora >= 1.3:
            alta_conf.append("🔐 Dupla chance: 1X (alta)")
        elif L_home < 4 and gols_home_casa >= 1.1 and sofre_home_casa <= 1.4 and sofre_away_fora >= 1.2:
            media_conf.append("🔐 Dupla chance: 1X (média)")
        if L_away < 3 and gols_away_fora >= 1.2 and sofre_away_fora <= 1.3 and sofre_home_casa >= 1.3:
            alta_conf.append("🔐 Dupla chance: X2 (alta)")
        elif L_away < 4 and gols_away_fora >= 1.1 and sofre_away_fora <= 1.4 and sofre_home_casa >= 1.2:
            media_conf.append("🔐 Dupla chance: X2 (média)")

        # Over 1.5
        marcou_home = "W" in form_home[:2] or "D" in form_home[:2]
        marcou_away = "W" in form_away[:2] or "D" in form_away[:2]
        if gm_home + gm_away >= 2.5 and gs_home + gs_away >= 2.0 and marcou_home and marcou_away:
            alta_conf.append("⚽ Over 1.5 gols (alta)")
        elif gm_home + gm_away >= 2.2 and gs_home + gs_away >= 2.0 and (marcou_home or marcou_away):
            media_conf.append("⚠️ Over 1.5 gols (média)")

        # Under 2.5
        if gm_home + gm_away < 1.5 and gs_home + gs_away < 1.5 and (shots_home + shots_away) < 5 and ("0" in form_home or "LL" in form_home or "0" in form_away or "LL" in form_away):
            alta_conf.append("🧱 Under 2.5 gols (alta)")
        elif gm_home + gm_away < 2.0 and gs_home + gs_away < 2.0 and (shots_home + shots_away) < 6 and ("0" in form_home or "LL" in form_home or "0" in form_away or "LL" in form_away):
            media_conf.append("🧱 Under 2.5 gols (média)")

        # Ambas NÃO Marcam
        if gm_home + gm_away < 1.5 and gs_home + gs_away < 1.5 and (clean_home + clean_away) > 4:
            alta_conf.append("❌ Ambas NÃO marcam (alta)")
        elif gm_home + gm_away < 1.8 and gs_home + gs_away < 1.8 and (clean_home + clean_away) > 3:
            media_conf.append("❌ Ambas NÃO marcam (média)")

        # Gol do Mandante
        marcou2_home = form_home[:2].count("W") + form_home[:2].count("D")
        marcou1_home = form_home[:1].count("W") + form_home[:1].count("D")
        if gols_home_casa >= 1.5 and sofre_away_fora >= 1.5 and marcou2_home == 2:
            alta_conf.append("⚽ Gol do Mandante (alta)")
        elif gols_home_casa >= 1.3 and sofre_away_fora >= 1.3 and marcou1_home == 1:
            media_conf.append("⚽ Gol do Mandante (média)")

        # Gol do Visitante
        marcou2_away = form_away[:2].count("W") + form_away[:2].count("D")
        marcou1_away = form_away[:1].count("W") + form_away[:1].count("D")
        if gols_away_fora >= 1.5 and sofre_home_casa >= 1.5 and marcou2_away == 2:
            alta_conf.append("⚽ Gol do Visitante (alta)")
        elif gols_away_fora >= 1.3 and sofre_home_casa >= 1.3 and marcou1_away == 1:
            media_conf.append("⚽ Gol do Visitante (média)")

        # Empate no intervalo
        if gm_home < 0.5 and gm_away < 0.5 and gs_home < 0.5 and gs_away < 0.5 and (shots_home + shots_away) < 5:
            if "D" in form_home or "D" in form_away:
                alta_conf.append("⏱️ Empate no 1º tempo (alta)")

        return "\n".join(alta_conf + media_conf) if alta_conf or media_conf else "Sem sugestão clara"
    except:
        return "Sem sugestão clara"

def sugestao_de_placar(stats_home, stats_away, sugestao_texto=""):
    try:
        def arred(v): return int(v) + 1 if v % 1 >= 0.8 else int(v)

        g_home = (
            float(stats_home["goals"]["for"]["average"].get("home", 0)) +
            float(stats_away["goals"]["against"]["average"].get("away", 0))
        ) / 2
        g_away = (
            float(stats_away["goals"]["for"]["average"].get("away", 0)) +
            float(stats_home["goals"]["against"]["average"].get("home", 0))
        ) / 2

        if "Dupla chance: 1X" in sugestao_texto:
            g_home += 0.5
        if "Dupla chance: X2" in sugestao_texto:
            g_away += 0.5
        if "Over 1.5" in sugestao_texto and g_home + g_away < 2:
            g_home += 0.5
        if "Under 3.5" in sugestao_texto and g_home + g_away > 3:
            excesso = g_home + g_away - 3
            g_home -= excesso / 2
            g_away -= excesso / 2
        if "Ambas NÃO marcam" in sugestao_texto:
            if g_home > g_away:
                g_away = 0
            else:
                g_home = 0
        if "Gol do Mandante" in sugestao_texto and g_home < 1:
            g_home = 1
        if "Gol do Visitante" in sugestao_texto and g_away < 1:
            g_away = 1

        g_home = max(0, arred(g_home))
        g_away = max(0, arred(g_away))
        alt = f"{g_home+1} x {g_away}" if g_home <= g_away else f"{g_home} x {g_away+1}"
        return f"{g_home} x {g_away} ou {alt}"
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

    sugestoes = gerar_sugestao(stats_home, stats_away)
    placar = sugestao_de_placar(stats_home, stats_away, sugestoes)

    dt = datetime.utcfromtimestamp(fixture["timestamp"]).astimezone(pytz.timezone("America/Sao_Paulo"))
    data = dt.strftime("%d/%m")
    hora = dt.strftime("%H:%M")

    salvar_resultado_previsto(
        fixture["id"], home["name"], away["name"],
        sugestoes.replace("\n", " | ") if sugestoes else "Sem sugestão clara"
    )

    return (
        f"⚽ *{home['name']} x {away['name']}*\n"
        f"🌍 {league['name']}\n"
        f"📅 {data} | 🕒 {hora}\n"
        f"📌 Status: {fixture['status']['short']}\n\n"
        f"🔢 *Placar provável:* {placar}\n\n"
        f"💡 *Sugestões de entrada:*\n{sugestoes}"
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
        if "Sem sugestão clara" in previsao:
            continue

        url = f"https://v3.football.api-sports.io/fixtures?id={jogo_id}"
        res = requests.get(url, headers=HEADERS).json()
        if not res["response"]:
            continue
        jogo = res["response"][0]
        if jogo["fixture"]["status"]["short"] != "FT":
            continue

        gols_home = jogo["goals"]["home"]
        gols_away = jogo["goals"]["away"]
        gols_ht_home = jogo["score"]["halftime"]["home"]
        gols_ht_away = jogo["score"]["halftime"]["away"]
        entradas = previsao.split(" | ")
        resultado = []

        for entrada in entradas:
            tipo = "alto" if "(alta" in entrada else "medio"
            acertou = False

            if "Over 1.5" in entrada and (gols_home + gols_away) >= 2:
                acertou = True
            if "Under 3.5" in entrada and (gols_home + gols_away) <= 3:
                acertou = True
            if "Under 2.5" in entrada and (gols_home + gols_away) <= 2:
                acertou = True
            if "Ambas NÃO marcam" in entrada and (gols_home == 0 or gols_away == 0):
                acertou = True
            if "Empate no 1º tempo" in entrada and gols_ht_home == gols_ht_away:
                acertou = True
            if "Dupla chance: 1X" in entrada and gols_home >= gols_away:
                acertou = True
            if "Dupla chance: X2" in entrada and gols_away >= gols_home:
                acertou = True
            if "Gol do Mandante" in entrada and gols_home >= 1:
                acertou = True
            if "Gol do Visitante" in entrada and gols_away >= 1:
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
    bot.send_message(chat_id=CHAT_ID, text=final.strip(), parse_mode="Markdown")

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="✅ Robô ativado com 8 estratégias e placares prováveis!")
    while True:
        verificar_pre_jogos()
        verificar_resultados()
        time.sleep(14400)
