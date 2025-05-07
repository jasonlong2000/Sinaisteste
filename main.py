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

    h2h = buscar_h2h(home["id"], away["id"])
    h2h_txt = '\n'.join([f"{f['teams']['home']['name']} {f['goals']['home']} x {f['goals']['away']} {f['teams']['away']['name']}" for f in h2h]) or "Sem confrontos recentes."

    # Odds
    odds_txt = ""
    odds = buscar_odds(fixture["id"])
    if odds:
        for book in odds[0].get("bookmakers", []):
            for bet in book.get("bets", []):
                if bet["name"] == "Match Winner":
                    odds_txt = '\n'.join([f"{o['value']}: {o['odd']}" for o in bet["values"]])

    # Sugestão
    try:
        s_home = float(gs_away)
        s_away = float(gs_home)
        m_home = float(gm_home)
        m_away = float(gm_away)
        sug = f"🎯 Placar provável: {round((m_home + s_away)/2)} x {round((m_away + s_home)/2)}"
    except:
        sug = "🎯 Placar provável: Indefinido"

    return (
        f"⚽ *{home_name} x {away_name}*\n"
        f"🌍 {league['name']}\n"
        f"📅 {data} | 🕒 {hora}\n"
        f"📌 Status: {fixture['status']['short']}\n"
        f"\n🎯 *Gols esperados:* {home_name}: {gm_home} / {away_name}: {gm_away}\n"
        f"❌ *Gols sofridos:* {home_name}: {gs_home} / {away_name}: {gs_away}\n"
        f"🚩 *Escanteios médios:* {home_name}: {esc_home} / {away_name}: {esc_away}\n"
        f"\n🤝 *Confrontos diretos:*\n{h2h_txt}\n"
        f"\n💡 *Odds pré-jogo:*\n{odds_txt or 'Indisponível'}\n"
        f"\n📈 *{sug}*"
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
        time.sleep(21600)  # Roda a cada 6h
