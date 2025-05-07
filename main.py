import requests
from datetime import datetime
from telegram import Bot
import pytz
import time
import os

# Configurações
API_KEY = "6810ea1e7c44dab18f4fc039b73e8dd2"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"
ARQUIVO_ENVIADOS = "pre_jogos_filtrados.txt"

bot = Bot(token=BOT_TOKEN)

# Lista com apenas os nomes das ligas
LIGAS_PERMITIDAS = [
    "Pro League", "Serie A", "Copa do Brasil", "Serie B", "Paulista",
    "Gaucho 1", "First League", "Premier League", "Community Shield",
    "Championship", "League Cup", "Premier League Summer Series",
    "EFL League One", "UEFA Champions League", "UEFA Europa League",
    "UEFA Super Cup", "UEFA Europa Conference League", "Ligue 1",
    "Coupe de la Ligue", "Bundesliga", "UEFA Euro Championship",
    "FIFA Confederations Cup", "UEFA Euro Qualifiers", "UEFA Nations League",
    "FIFA Club World Cup", "Copa America", "Olympics", "Serie A",
    "La Liga", "Copa del Rey", "Supercopa de Espana", "MLS",
    "Copa Libertadores", "Copa Sudamericana", "Recopa Sudamericana"
]

def carregar_enviados():
    if os.path.exists(ARQUIVO_ENVIADOS):
        with open(ARQUIVO_ENVIADOS, "r") as f:
            return set(line.strip() for line in f)
    return set()

def salvar_enviado(jogo_id):
    with open(ARQUIVO_ENVIADOS, "a") as f:
        f.write(f"{jogo_id}\n")

def buscar_jogos():
    hoje = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={hoje}"
    headers = {"x-apisports-key": API_KEY}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json().get("response", [])
    except Exception as e:
        print(f"Erro ao buscar jogos: {e}")
        return []

def formatar_jogo(jogo):
    fixture = jogo["fixture"]
    teams = jogo["teams"]
    league = jogo["league"]

    home = teams["home"]["name"]
    away = teams["away"]["name"]
    liga = league["name"]
    pais = league["country"]
    local = fixture["venue"]["name"]
    timestamp = fixture["timestamp"]

    try:
        fuso = pytz.timezone("America/Sao_Paulo")
        dt = datetime.utcfromtimestamp(timestamp).astimezone(fuso)
        data = dt.strftime("%d/%m")
        hora = dt.strftime("%H:%M")
    except:
        data, hora = "?", "?"

    return (
        f"⚽ {home} x {away}\n"
        f"🌍 {liga} ({pais})\n"
        f"🏟️ Local: {local}\n"
        f"📅 Data: {data} | 🕒 Horário: {hora}\n"
        f"📌 Status: Not Started"
    )

def verificar_jogos():
    enviados = carregar_enviados()
    jogos = buscar_jogos()
    novos = 0

    try:
        bot.send_message(chat_id=CHAT_ID, text="🔎 Verificando *pré-jogos* das ligas selecionadas...", parse_mode="Markdown")
    except: pass

    for jogo in jogos:
        fixture = jogo["fixture"]
        league = jogo["league"]
        jogo_id = str(fixture["id"])
        status = fixture["status"]["short"]
        nome_liga = league["name"]

        if status != "NS" or jogo_id in enviados or nome_liga not in LIGAS_PERMITIDAS:
            continue

        try:
            mensagem = formatar_jogo(jogo)
            bot.send_message(chat_id=CHAT_ID, text=mensagem)
            salvar_enviado(jogo_id)
            novos += 1
            time.sleep(2)
        except Exception as e:
            print(f"Erro ao enviar jogo {jogo_id}: {e}")
            time.sleep(5)

    if novos == 0:
        try:
            bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo encontrado nas ligas selecionadas.", parse_mode="Markdown")
        except: pass

if __name__ == "__main__":
    while True:
        verificar_jogos()
        time.sleep(21600)  # Verifica a cada 6 horas
