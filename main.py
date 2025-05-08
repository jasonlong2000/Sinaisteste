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
        btts_home = float(btts_home.strip('%'))
        btts_away = float(btts_away.strip('%'))
        clean_home = int(clean_home)
        clean_away = int(clean_away)
        first_goal_home = float(first_goal_home.strip('%'))
        first_goal_away = float(first_goal_away.strip('%'))
        shots_home = float(shots_home)
        shots_away = float(shots_away)
        over25_home = float(over25_home.strip('%'))
        over25_away = float(over25_away.strip('%'))
        shots_on_home = float(shots_on_home)
        shots_on_away = float(shots_on_away)
        gs_home = float(gs_home)
        gs_away = float(gs_away)
        over15_home = float(over15_home.strip('%'))
        over15_away = float(over15_away.strip('%'))

        sugestoes = []
        total_gols = gm_home + gm_away
        shots_total = shots_home + shots_away
        shots_on_total = shots_on_home + shots_on_away
        btts_media = (btts_home + btts_away) / 2

        print(\"DEBUG MÉTRICAS:\", {
            \"Gols Esperados\": total_gols,
            \"Over 1.5\": (over15_home, over15_away),
            \"Over 2.5\": (over25_home, over25_away),
            \"BTTS%\": btts_media,
            \"Finalizações no Alvo\": shots_on_total
        })

        if over25_home >= 65 and over25_away >= 65 and total_gols >= 2.6 and btts_media >= 60 and shots_on_total >= 8:
            sugestoes.append(\"⚽ Mais de 2.5 gols\")

        if over15_home >= 70 and over15_away >= 70 and total_gols >= 2.0 and btts_media >= 60 and shots_on_total >= 7:
            sugestoes.append(\"⚽ Mais de 1.5 gols\")

        if shots_total >= 20:
            sugestoes.append(\"🎯 Jogo com alta média de finalizações\")
        if clean_home + clean_away >= 8:
            sugestoes.append(\"🧤 Tendência de placar magro ou Under\")
        if first_goal_home >= 60:
            sugestoes.append(\"⚡ Mandante costuma marcar primeiro\")
        if first_goal_away >= 60:
            sugestoes.append(\"⚡ Visitante costuma marcar primeiro\")

        if (gm_home >= 1.5 and gs_away >= 1.2 and first_goal_home >= 60 and clean_home >= 3 and
            gm_home - gm_away > 0.8 and gs_away - gs_home > 0.5):
            sugestoes.append(\"🏆 Vitória provável: Mandante\")

        elif (gm_away >= 1.5 and gs_home >= 1.2 and first_goal_away >= 60 and clean_away >= 3 and
              gm_away - gm_home > 0.8 and gs_home - gs_away > 0.5):
            sugestoes.append(\"🏆 Vitória provável: Visitante\")

        return \"\\n\".join(sugestoes) if sugestoes else \"Sem sugestão clara\"
    except:
        return \"Sem sugestão clara\"
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
        f"📅 {data} | 🕒 {hora}\n"
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

    try:
        bot.send_message(chat_id=CHAT_ID, text="🔎 Verificando *jogos do dia* (pré-jogo)...", parse_mode="Markdown")
    except: pass

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
        try:
            bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo hoje nas ligas selecionadas.", parse_mode="Markdown")
        except: pass

if __name__ == "__main__":
    while True:
        verificar_pre_jogos()
        time.sleep(21600)  # Executa a cada 6 horas (21600 segundos)
