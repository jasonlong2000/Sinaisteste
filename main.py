import requests
from datetime import datetime
from telegram import Bot
import pytz
import time
import os

# Suas chaves
API_KEY = "6810ea1e7c44dab18f4fc039b73e8dd2"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"
ARQUIVO_ENVIADOS = "pre_jogos_filtrados.txt"

# Iniciar bot
bot = Bot(token=BOT_TOKEN)

# Ligas permitidas
LIGAS_PERMITIDAS = [
    "Belgium - Pro League", "Brazil - Serie A", "Brazil - Copa do Brasil",
    "Brazil - Serie B", "Brazil - Paulista", "Brazil - Gaucho 1",
    "Bulgaria - First League", "England - Premier League", "England - Community Shield",
    "England - Championship", "England - League Cup", "England - Premier League Summer Series",
    "England - EFL League One", "UEFA Champions League", "UEFA Europa League",
    "UEFA Super Cup", "UEFA Europa Conference League", "France - Ligue 1",
    "France - Coupe de la Ligue", "Germany - Bundesliga", "UEFA Euro Championship",
    "FIFA Confederations Cup", "UEFA Euro Qualifiers", "UEFA Nations League",
    "FIFA Club World Cup", "Copa America", "Olympics", "Italy - Serie A",
    "Spain - La Liga", "Spain - Copa del Rey", "Spain - Supercopa de Espana",
    "USA - MLS", "Copa Libertadores", "Copa Sudamericana", "Recopa Sudamericana"
]

# Gerencia enviados
def carregar_enviados():
    if os.path.exists(ARQUIVO_ENVIADOS):
        with open(ARQUIVO_ENVIADOS, "r") as f:
            return set(line.strip() for line in f)
    return set()

def salvar_enviado(jogo_id):
    with open(ARQUIVO_ENVIADOS, "a") as f:
        f.write(f"{jogo_id}\n")

# Consulta a API-Football
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

# Monta mensagem para Telegram
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

# Loop de verificação
def verificar_jogos():
    enviados = carregar_enviados()
    jogos = buscar_jogos()
    novos = 0

    try:
        bot.send_message(chat_id=CHAT_ID, text="🔎 Verificando *jogos do dia* com status Not Started...", parse_mode="Markdown")
    except: pass

    for jogo in jogos:
        fixture = jogo["fixture"]
        league = jogo["league"]
        jogo_id = str(fixture["id"])
        status = fixture["status"]["short"]
        nome_completo = f"{league['name']}" if "International" not in league["country"] else f"{league['country']} - {league['name']}"

        if status != "NS" or jogo_id in enviados or nome_completo not in LIGAS_PERMITIDAS:
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

# Loop contínuo
if __name__ == "__main__":
    while True:
        verificar_jogos()
        time.sleep(21600)  # Executa a cada 6 horas
