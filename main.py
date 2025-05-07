import requests
from datetime import datetime
from telegram import Bot
import time
import os

# Configurações
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"
LEAGUE_IDS = [12321]  # Champions League apenas
ARQUIVO_ENVIADOS = "sinais_ao_vivo.txt"

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
    except Exception as e:
        print(f"Erro liga {league_id}: {e}")
        return []

def fetch_details(match_id):
    url = f"https://api.football-data-api.com/match?key={API_KEY}&match_id={match_id}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("data", {})
    except:
        return {}

def formatar(jogo, detalhes):
    home = jogo.get("home_name", "Time A")
    away = jogo.get("away_name", "Time B")
    minuto = jogo.get("minute", "-")
    liga = jogo.get("league_name", "Liga")

    gols_a = detalhes.get("team_a_goal_count", "-")
    gols_b = detalhes.get("team_b_goal_count", "-")
    escanteios_a = detalhes.get("team_a_corners", "-")
    escanteios_b = detalhes.get("team_b_corners", "-")
    chutes_a = detalhes.get("team_a_shots", "-")
    chutes_b = detalhes.get("team_b_shots", "-")
    posse_a = detalhes.get("team_a_possession", "-")
    posse_b = detalhes.get("team_b_possession", "-")
    amarelos_a = detalhes.get("team_a_yellow_cards", "-")
    amarelos_b = detalhes.get("team_b_yellow_cards", "-")

    return (
        f"⚽ *Jogo ao vivo!*
"
        f"🏟️ {home} x {away}
"
        f"Liga: {liga} | ⏱️ Minuto: {minuto}

"
        f"📊 *Estatísticas da Partida:*
"
        f"🎯 Gols: {home}: {gols_a} | {away}: {gols_b}
"
        f"🚩 Escanteios: {home}: {escanteios_a} | {away}: {escanteios_b}
"
        f"🔫 Chutes: {home}: {chutes_a} | {away}: {chutes_b}
"
        f"⚖️ Posse de Bola: {home}: {posse_a}% | {away}: {posse_b}%
"
        f"🟨 Cartões Amarelos: {home}: {amarelos_a} | {away}: {amarelos_b}")

def monitorar():
    enviados = carregar_enviados()
    houve_jogo = False

    print("✅ Bot rodando...")
    try:
        bot.send_message(chat_id=CHAT_ID, text="🔁 Verificando *jogos ao vivo* da Champions League...", parse_mode="Markdown")
    except: pass

    for league_id in LEAGUE_IDS:
        jogos = fetch_matches(league_id)
        for jogo in jogos:
            minuto = jogo.get("minute", 0)
            if not isinstance(minuto, int) or minuto <= 0:
                continue

            jogo_id = str(jogo.get("id"))
            chave = f"{jogo_id}_{minuto}"
            if chave in enviados:
                continue

            detalhes = fetch_details(jogo_id)
            mensagem = formatar(jogo, detalhes)

            try:
                bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
                salvar_enviado(chave)
                enviados.add(chave)
                houve_jogo = True
                time.sleep(2)
            except Exception as e:
                print(f"Erro ao enviar {jogo_id}: {e}")
                time.sleep(5)

    if not houve_jogo:
        try:
            bot.send_message(chat_id=CHAT_ID, text="🔍 Nenhum *jogo ao vivo* encontrado nesta verificação.", parse_mode="Markdown")
        except: pass

if __name__ == "__main__":
    while True:
        monitorar()
        time.sleep(300)  # Verifica a cada 5 minutos
