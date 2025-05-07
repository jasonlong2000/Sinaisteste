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

def buscar_h2h(home_id, away_id):
    url = f"https://v3.football.api-sports.io/fixtures/headtohead?h2h={home_id}-{away_id}&last=3"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.json().get("response", [])
    except:
        return []

def buscar_odds(fixture_id):
    url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.json().get("response", [])
    except:
        return []

def gerar_sugestoes(gm_home, gm_away, gs_home, gs_away, esc_home, esc_away):
    sugestoes = []
    try:
        gm1 = float(gm_home)
        gm2 = float(gm_away)
        gs1 = float(gs_home)
        gs2 = float(gs_away)
        total_gols = gm1 + gm2
        total_esc = float(esc_home) + float(esc_away)

        if gm1 > 1.5 and gs2 > 1.0:
            sugestoes.append("🏆 Vitória do time da casa")
        if gm2 > 1.2 and gs1 > 1.0:
            sugestoes.append("🛡️ Dupla chance visitante")
        if total_gols > 2.7:
            sugestoes.append("🔥 Mais de 2.5 gols")
        if gm1 > 1.0 and gm2 > 1.0:
            sugestoes.append("⚔️ Ambos marcam")
        if total_esc >= 8.5:
            sugestoes.append("🚩 Mais de 8.5 escanteios")
        sugestoes.append("🟨 Mais de 4.5 cartões")  # padrão

    except:
        return "Sem sugestão clara"

    return '\n'.join(sugestoes) if sugestoes else "Sem sugestão"

def gerar_sugestoes(gm_home, gm_away, gs_home, gs_away, esc_home, esc_away):
    sugestoes = []
    try:
        gm1 = float(gm_home)
        gm2 = float(gm_away)
        gs1 = float(gs_home)
        gs2 = float(gs_away)
        total_gols = gm1 + gm2
        total_esc = float(esc_home) + float(esc_away)

        if gm1 > 1.5 and gs2 > 1.0:
            sugestoes.append("🏆 Vitória do time da casa")
        if gm2 > 1.2 and gs1 > 1.0:
            sugestoes.append("🛡️ Dupla chance visitante")
        if total_gols > 2.7:
            sugestoes.append("🔥 Mais de 2.5 gols")
        if gm1 > 1.0 and gm2 > 1.0:
            sugestoes.append("⚔️ Ambos marcam")
        if total_esc >= 8.5:
            sugestoes.append("🚩 Mais de 8.5 escanteios")
        sugestoes.append("🟨 Mais de 4.5 cartões")

    except:
        return "Sem sugestão clara"

    return '\n'.join(sugestoes) if sugestoes else "Sem sugestão"


def formatar_jogo(jogo):
    fixture = jogo["fixture"]
    teams = jogo["teams"]
    league = jogo["league"]
    home = teams["home"]
    away = teams["away"]

    home_name = home["name"]
    away_name = away["name"]
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

    gm_home = stats_home.get("goals", {}).get("for", {}).get("average", {}).get("total", "-")
    gs_home = stats_home.get("goals", {}).get("against", {}).get("average", {}).get("total", "-")
    gm_away = stats_away.get("goals", {}).get("for", {}).get("average", {}).get("total", "-")
    gs_away = stats_away.get("goals", {}).get("against", {}).get("average", {}).get("total", "-")
    esc_home = stats_home.get("corners", {}).get("average", {}).get("total", "-")
    esc_away = stats_away.get("corners", {}).get("average", {}).get("total", "-")

    sugestao = gerar_sugestoes(gm_home, gm_away, gs_home, gs_away, esc_home, esc_away)

    return (
        f"\u26bd *{home_name} x {away_name}*\n"
        f"🌍 {league['name']}\n"
        f"📅 {data} | 🕒 {hora}\n"
        f"📌 Status: {fixture['status']['short']}\n"
        f"\n🎯 *Gols esperados:* {home_name}: {gm_home} | {away_name}: {gm_away}\n"
        f"❌ *Gols sofridos:* {home_name}: {gs_home} | {away_name}: {gs_away}\n"
        f"🚩 *Escanteios médios:* {home_name}: {esc_home} | {away_name}: {esc_away}\n"
        f"\n💡 *Sugestões de entrada:*\n{sugestao}"
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
        league = jogo["league"]
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
            bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo hoje.", parse_mode="Markdown")
        except: pass

if __name__ == "__main__":
    while True:
        verificar_pre_jogos()
        time.sleep(21600)
