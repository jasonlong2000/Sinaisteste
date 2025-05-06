import requests
from datetime import datetime, timedelta
from telegram import Bot
import pytz
import time
import os

API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
CHAT_ID = "-1002675165012"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"

LEAGUE_IDS = [2010, 2007, 2055, 2008, 2012, 2013, 2022, 2015, 2045, 2016, 2051, 2070,
    2017, 12321, 12322, 12325, 12323, 2003, 2063, 2006, 12330, 12328, 12329,
    12332, 12327, 12324, 12331, 2005, 2004, 2039, 2040, 2020, 12333, 12334, 12335]

ARQUIVO_ENVIADOS = "enviados.txt"
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
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        print(f"Erro na liga {league_id}: {e}")
        return []

def fetch_match_details(match_id):
    url = f"https://api.football-data-api.com/match?key={API_KEY}&match_id={match_id}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("data", {})
    except Exception as e:
        print(f"Erro ao buscar detalhes do jogo {match_id}: {e}")
        return {}

def formatar_jogo(jogo, detalhes):
    home = jogo.get("home_name", "Time A")
    away = jogo.get("away_name", "Time B")
    status = jogo.get("status", "-").upper()
    minuto = jogo.get("minute", "-")
    liga = jogo.get("league_name", "Liga")
    fase = jogo.get("stage_name", "-")
    timestamp = jogo.get("date_unix", 0)

    try:
        zona = pytz.timezone("America/Sao_Paulo")
        dt = datetime.utcfromtimestamp(timestamp).astimezone(zona)
        data = dt.strftime('%d/%m')
        hora = dt.strftime('%H:%M')
    except:
        data, hora = "?", "?"

    # Dados detalhados
    escanteios_a = detalhes.get("team_a_corners", "-")
    escanteios_b = detalhes.get("team_b_corners", "-")
    chutes_a = detalhes.get("team_a_shots", "-")
    chutes_b = detalhes.get("team_b_shots", "-")
    posse_a = detalhes.get("team_a_possession", "-")
    posse_b = detalhes.get("team_b_possession", "-")
    amarelos_a = detalhes.get("team_a_yellow_cards", "-")
    amarelos_b = detalhes.get("team_b_yellow_cards", "-")

    return (
        f"⚽ {home} x {away}\n"
        f"Liga: {liga} | Fase: {fase}\n"
        f"Status: {status} | Minuto: {minuto} | Data: {data} | Horário: {hora}\n\n"
        f"📊 Estatísticas:\n"
        f"- Escanteios: {home}: {escanteios_a} | {away}: {escanteios_b}\n"
        f"- Chutes: {home}: {chutes_a} | {away}: {chutes_b}\n"
        f"- Posse de bola: {home}: {posse_a}% | {away}: {posse_b}%\n"
        f"- Cartões Amarelos: {home}: {amarelos_a} | {away}: {amarelos_b}"
    )

def executar():
    enviados = carregar_enviados()
    try:
        bot.send_message(chat_id=CHAT_ID, text="🚀 Bot iniciado!\n📅 Verificando jogos de hoje...")
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
            data_jogo = datetime.utcfromtimestamp(timestamp).astimezone(pytz.timezone("America/Sao_Paulo")).date()

            if data_jogo != hoje or jogo_id in enviados:
                continue

            detalhes = fetch_match_details(jogo_id)
            texto = formatar_jogo(jogo, detalhes)

            try:
                bot.send_message(chat_id=CHAT_ID, text=texto)
                salvar_enviado(jogo_id)
                enviados.add(jogo_id)
                novos += 1
                time.sleep(2)
            except Exception as e:
                print(f"Erro ao enviar jogo {jogo_id}: {e}")
                time.sleep(5)

    if novos == 0:
        try:
            bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo encontrado hoje nas ligas configuradas.")
        except Exception as e:
            print(f"Erro ao enviar mensagem final: {e}")

if __name__ == "__main__":
    while True:
        executar()
        time.sleep(21600)  # 6 horas
