import requests
from datetime import datetime, timedelta
from telegram import Bot
import time
import os
import pytz

API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
CHAT_ID = "-1002675165012"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"

LEAGUE_IDS = [
    2010, 2007, 2055, 2008, 2012, 2013, 2022, 2015, 2045, 2016, 2051, 2070,
    2017, 12321, 12322, 12325, 12323, 2003, 2063, 2006, 12330, 12328, 12329,
    12332, 12327, 12324, 12331, 2005, 2004, 2039, 2040, 2020, 12333, 12334, 12335
]

ARQUIVO_ENVIADOS = "enviados.txt"
bot = Bot(token=BOT_TOKEN)

# Carregar IDs já enviados
def carregar_enviados():
    if os.path.exists(ARQUIVO_ENVIADOS):
        with open(ARQUIVO_ENVIADOS, "r") as f:
            return set(line.strip() for line in f)
    return set()

# Salvar novo ID
def salvar_enviado(jogo_id):
    with open(ARQUIVO_ENVIADOS, "a") as f:
        f.write(f"{jogo_id}\n")

enviados = carregar_enviados()

def fetch_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"Erro ao consultar liga {league_id}: {e}")
        return []

def formatar_jogo(jogo):
    home = jogo.get("home_name", "Time A")
    away = jogo.get("away_name", "Time B")
    status = jogo.get("status", "-").upper()
    minuto = jogo.get("minute", "-")
    liga = jogo.get("league_name", "Liga")
    fase = jogo.get("stage_name", "-")
    timestamp = jogo.get("date_unix", 0)
    
    try:
        brasília = pytz.timezone("America/Sao_Paulo")
        dt_brasilia = datetime.utcfromtimestamp(timestamp).astimezone(brasília)
        data = dt_brasilia.strftime('%d/%m')
        hora = dt_brasilia.strftime('%H:%M')
    except:
        data, hora = "?", "?"
    
    return (
        f"⚽ {home} x {away}\n"
        f"Liga: {liga} | Fase: {fase}\n"
        f"Status: {status} | Minuto: {minuto} | Data: {data} | Horário: {hora}"
    )

def main():
    try:
        bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado!\n📅 Verificando jogos do dia...")
    except Exception as e:
        print(f"Erro ao enviar mensagem inicial: {e}")
        return

    novos = 0
    hoje = datetime.now(pytz.timezone("America/Sao_Paulo")).date()

    for league_id in LEAGUE_IDS:
        jogos = fetch_matches(league_id)
        for jogo in jogos:
            jogo_id = str(jogo.get("id"))
            timestamp = jogo.get("date_unix", 0)
            dt_jogo = datetime.utcfromtimestamp(timestamp).astimezone(pytz.timezone("America/Sao_Paulo")).date()
            
            if dt_jogo != hoje:
                continue

            if jogo_id and jogo_id not in enviados:
                try:
                    texto = formatar_jogo(jogo)
                    bot.send_message(chat_id=CHAT_ID, text=texto)
                    enviados.add(jogo_id)
                    salvar_enviado(jogo_id)
                    novos += 1
                    time.sleep(2)
                except Exception as e:
                    print(f"Erro ao enviar jogo {jogo_id}: {e}")
                    time.sleep(5)

    if novos == 0:
        try:
            bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo encontrado para hoje nas ligas configuradas.")
        except Exception as e:
            print(f"Erro ao enviar mensagem final: {e}")

if __name__ == "__main__":
    main()
