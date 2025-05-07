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

    headers = {
        "x-apisports-key": API_KEY
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json().get("response", [])
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
    status = fixture["status"]["short"]
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
        f"📌 Status: {status}"
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
            bot.send_message(chat_id=CHAT_ID, text=mensagem)
            salvar_enviado(jogo_id)
            novos += 1
            time.sleep(2)
        except Exception as e:
            print(f"Erro ao enviar jogo {jogo_id}: {e}")
            time.sleep(5)

    if novos == 0:
        try:
            bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo com status *Not Started* encontrado hoje.", parse_mode="Markdown")
        except: pass

if __name__ == "__main__":
    while True:
        verificar_pre_jogos()
        time.sleep(21600)  # Executa a cada 6 horas
