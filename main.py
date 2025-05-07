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

# IDs das ligas desejadas
LIGAS_IDS = [2, 11, 13]  # Champions, Sudamericana, Libertadores

# Status considerados não finalizados
STATUS_ACEITOS = {"NS", "TBD", "1H", "2H", "HT", "ET", "P", "INT", "LIVE", "BREAK"}

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
    headers = {"x-apisports-key": API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=15)
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

    gols_home = jogo.get("goals", {}).get("home", "-")
    gols_away = jogo.get("goals", {}).get("away", "-")
    rodada = fixture.get("round", "-")
    arbitragem = fixture.get("referee", "-")

    try:
        fuso = pytz.timezone("America/Sao_Paulo")
        dt = datetime.utcfromtimestamp(timestamp).astimezone(fuso)
        data = dt.strftime("%d/%m")
        hora = dt.strftime("%H:%M")
    except:
        data, hora = "?", "?"

    return (
        f"\u26bd {home} {gols_home} x {gols_away} {away}\n"
        f"\U0001F30D {liga} ({pais})\n"
        f"\U0001F3DF️ Estádio: {local or 'Indefinido'}\n"
        f"\u2b55 Status: {status} | \ud83d\udcc5 {data} | \ud83d\udd52 {hora}\n"
        f"\u26a1 Rodada: {rodada} | ⚖️ Árbitro: {arbitragem}"
    )

def verificar_jogos_nao_finalizados():
    enviados = carregar_enviados()
    jogos = buscar_jogos_do_dia()
    novos = 0

    print("🔄 Verificando jogos do dia (não finalizados)...")
    try:
        bot.send_message(chat_id=CHAT_ID, text="\ud83d\udd0e Listando jogos *não finalizados* de hoje...", parse_mode="Markdown")
    except: pass

    for jogo in jogos:
        fixture = jogo["fixture"]
        league = jogo["league"]
        jogo_id = str(fixture["id"])
        status = fixture["status"]["short"]
        league_id = league.get("id")

        if jogo_id in enviados or league_id not in LIGAS_IDS or status not in STATUS_ACEITOS:
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
            bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo *não finalizado* encontrado hoje nas ligas selecionadas.", parse_mode="Markdown")
        except: pass

if __name__ == "__main__":
    while True:
        verificar_jogos_nao_finalizados()
        time.sleep(21600)  # Executa a cada 6 horas
