import requests
from datetime import datetime
from telegram import Bot
import pytz
import time
import os

API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
CHAT_ID = "-1002675165012"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"

LEAGUE_IDS = [
    2010, 2007, 2055, 2008, 2012, 2013, 2022, 2015, 2045, 2016,
    2051, 2070, 2017, 12321, 12322, 12325, 12323, 2003, 2063, 2006,
    12330, 12328, 12329, 12332, 12327, 12324, 12331, 2005, 2004,
    2039, 2040, 2020, 12333, 12334, 12335
]

ARQUIVO_ENVIADOS = "jogos_dia_enviados.txt"
bot = Bot(token=BOT_TOKEN)

def carregar_enviados():
    if os.path.exists(ARQUIVO_ENVIADOS):
        with open(ARQUIVO_ENVIADOS, "r") as f:
            return set(line.strip() for line in f)
    return set()

def salvar_enviado(jogo_id):
    with open(ARQUIVO_ENVIADOS, "a") as f:
        f.write(f"{jogo_id}\n")

def fetch_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        return res.json().get("data", [])
    except Exception as e:
        print(f"Erro liga {league_id}: {e}")
        return []

def formatar_jogo(jogo):
    home = jogo.get("home_name", "Time A")
    away = jogo.get("away_name", "Time B")
    status = jogo.get("status", "-").upper()
    liga = jogo.get("league_name", "Liga")
    estadio = jogo.get("stadium_name", "Local não informado")
    timestamp = jogo.get("date_unix", 0)

    try:
        fuso = pytz.timezone("America/Sao_Paulo")
        dt = datetime.utcfromtimestamp(timestamp).astimezone(fuso)
        data = dt.strftime('%d/%m')
        hora = dt.strftime('%H:%M')
    except:
        data, hora = "?", "?"

    return (
        f"⚽ {home} x {away}\n"
        f"Liga: {liga} | Estádio: {estadio}\n"
        f"Status: {status} | Data: {data} | Horário: {hora}"
    )

def verificar_jogos_dia():
    enviados = carregar_enviados()
    novos = 0
    hoje = datetime.now(pytz.timezone("America/Sao_Paulo")).date()

    try:
        bot.send_message(chat_id=CHAT_ID, text="🗓️ Buscando jogos *do dia* com status INCOMPLETE...", parse_mode="Markdown")
    except: pass

    for league_id in LEAGUE_IDS:
        jogos = fetch_matches(league_id)
        for jogo in jogos:
            if jogo.get("status") != "incomplete":
                continue
            jogo_id = str(jogo.get("id"))
            if jogo_id in enviados:
                continue

            timestamp = jogo.get("date_unix", 0)
            data_jogo = datetime.utcfromtimestamp(timestamp).astimezone(pytz.timezone("America/Sao_Paulo")).date()

            if data_jogo != hoje:
                continue

            try:
                mensagem = formatar_jogo(jogo)
                bot.send_message(chat_id=CHAT_ID, text=mensagem)
                salvar_enviado(jogo_id)
                enviados.add(jogo_id)
                novos += 1
                time.sleep(2)
            except Exception as e:
                print(f"Erro ao enviar {jogo_id}: {e}")
                time.sleep(5)

    if novos == 0:
        try:
            bot.send_message(chat_id=CHAT_ID, text="❌ Nenhum jogo *do dia* com status INCOMPLETE encontrado.", parse_mode="Markdown")
        except: pass

if __name__ == "__main__":
    while True:
        verificar_jogos_dia()
        time.sleep(21600)  # A cada 6 horas
