import requests
from datetime import datetime
from telegram import Bot
import time
import os

API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"

CHAMPIONS = 12321  # ID da Champions League
ARQUIVO_ENVIADOS = "ao_vivo_champions.txt"
bot = Bot(token=BOT_TOKEN)

def carregar_enviados():
    if os.path.exists(ARQUIVO_ENVIADOS):
        with open(ARQUIVO_ENVIADOS, "r") as f:
            return set(line.strip() for line in f)
    return set()

def salvar_enviado(jogo_id, minuto):
    with open(ARQUIVO_ENVIADOS, "a") as f:
        f.write(f"{jogo_id}_{minuto}\n")

def fetch_live_matches():
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={CHAMPIONS}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json().get("data", [])
    except Exception as e:
        print(f"Erro na requisição: {e}")
        return []

def fetch_match_details(match_id):
    url = f"https://api.football-data-api.com/match?key={API_KEY}&match_id={match_id}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json().get("data", {})
    except Exception as e:
        print(f"Erro nos detalhes do jogo {match_id}: {e}")
        return {}

def formatar_mensagem(jogo, detalhes):
    home = jogo.get("home_name", "Time A")
    away = jogo.get("away_name", "Time B")
    minuto = jogo.get("minute", "-")
    liga = jogo.get("league_name", "Liga")

    # Dados estatísticos
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
        f"📊 Estatísticas:\n"
        f"- Escanteios: {home}: {escanteios_a} | {away}: {escanteios_b}\n"
        f"- Chutes: {home}: {chutes_a} | {away}: {chutes_b}\n"
        f"- Posse de bola: {home}: {posse_a}% | {away}: {posse_b}%\n"
        f"- Cartões Amarelos: {home}: {amarelos_a} | {away}: {amarelos_b}"
    )

def monitorar():
    enviados = carregar_enviados()
    houve_entrada = False

    print("🔍 Buscando jogos AO VIVO da Champions League...")

    try:
        bot.send_message(chat_id=CHAT_ID, text="🔄 Buscando *jogos ao vivo* da Champions League...", parse_mode="Markdown")
    except Exception as e:
        print(f"Erro no envio da mensagem inicial: {e}")

    jogos = fetch_live_matches()
    for jogo in jogos:
        if jogo.get("status") != "inplay":
            continue

        jogo_id = str(jogo.get("id"))
        minuto = str(jogo.get("minute", "-"))
        chave = f"{jogo_id}_{minuto}"

        if chave in enviados:
            continue

        detalhes = fetch_match_details(jogo_id)
        mensagem = formatar_mensagem(jogo, detalhes)

        try:
            bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
            salvar_enviado(jogo_id, minuto)
            enviados.add(chave)
            houve_entrada = True
            time.sleep(3)
        except Exception as e:
            print(f"Erro ao enviar jogo {jogo_id}: {e}")
            time.sleep(5)

    if not houve_entrada:
        try:
            bot.send_message(chat_id=CHAT_ID, text="❌ Nenhum *jogo ao vivo* encontrado na Champions League.", parse_mode="Markdown")
        except Exception as e:
            print(f"Erro ao enviar mensagem de status: {e}")

if __name__ == "__main__":
    while True:
        monitorar()
        time.sleep(300)  # Verifica a cada 5 minutos
