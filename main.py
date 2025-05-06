import requests
from datetime import datetime
from telegram import Bot
import pytz
import time
import os

# Configurações
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"
ARQUIVO_ENVIADOS = "ao_vivo_enviados.txt"

LEAGUE_IDS = [
    12321  # Champions League — você pode adicionar mais IDs aqui
]

bot = Bot(token=BOT_TOKEN)

def carregar_enviados():
    if os.path.exists(ARQUIVO_ENVIADOS):
        with open(ARQUIVO_ENVIADOS, "r") as f:
            return set(line.strip() for line in f)
    return set()

def salvar_enviado(chave):
    with open(ARQUIVO_ENVIADOS, "a") as f:
        f.write(f"{chave}\n")

def fetch_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json().get("data", [])
    except:
        return []

def fetch_details(match_id):
    url = f"https://api.football-data-api.com/match?key={API_KEY}&match_id={match_id}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json().get("data", {})
    except:
        return {}

def formatar_mensagem(jogo, detalhes):
    home = jogo.get("home_name", "Time A")
    away = jogo.get("away_name", "Time B")
    minuto = jogo.get("minute", "-")
    liga = jogo.get("league_name", "Liga")

    # Estatísticas
    escanteios_a = detalhes.get("team_a_corners", "-")
    escanteios_b = detalhes.get("team_b_corners", "-")
    chutes_a = detalhes.get("team_a_shots", "-")
    chutes_b = detalhes.get("team_b_shots", "-")
    posse_a = detalhes.get("team_a_possession", "-")
    posse_b = detalhes.get("team_b_possession", "-")
    amarelos_a = detalhes.get("team_a_yellow_cards", "-")
    amarelos_b = detalhes.get("team_b_yellow_cards", "-")

    return (
        f"⚽ *Jogo ao vivo!*\n"
        f"🏟️ {home} x {away}\n"
        f"Liga: {liga} | ⏱️ Minuto: {minuto}\n\n"
        f"📊 *Estatísticas:*\n"
        f"- Escanteios: {home}: {escanteios_a} | {away}: {escanteios_b}\n"
        f"- Chutes: {home}: {chutes_a} | {away}: {chutes_b}\n"
        f"- Posse de bola: {home}: {posse_a}% | {away}: {posse_b}%\n"
        f"- Cartões Amarelos: {home}: {amarelos_a} | {away}: {amarelos_b}"
    )

def monitorar():
    enviados = carregar_enviados()
    houve_jogo = False

    print("⏱️ Buscando partidas AO VIVO...")
    try:
        bot.send_message(chat_id=CHAT_ID, text="🔄 Bot ativo. Verificando jogos *ao vivo*...", parse_mode="Markdown")
    except: pass

    for league_id in LEAGUE_IDS:
        jogos = fetch_matches(league_id)
        for jogo in jogos:
            if jogo.get("status") != "inplay":
                continue

            jogo_id = str(jogo.get("id"))
            minuto = str(jogo.get("minute", "-"))
            chave = f"{jogo_id}_{minuto}"

            if chave in enviados:
                continue

            detalhes = fetch_details(jogo_id)
            msg = formatar_mensagem(jogo, detalhes)

            try:
                bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
                salvar_enviado(chave)
                enviados.add(chave)
                houve_jogo = True
                time.sleep(2)
            except:
                time.sleep(5)

    if not houve_jogo:
        try:
            bot.send_message(chat_id=CHAT_ID, text="🔍 Nenhum jogo *ao vivo* encontrado nesta verificação.", parse_mode="Markdown")
        except: pass

if __name__ == "__main__":
    while True:
        monitorar()
        time.sleep(300)  # Verifica a cada 5 minutos
