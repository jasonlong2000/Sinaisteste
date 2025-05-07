import requests
from datetime import datetime, timedelta
from telegram import Bot
import pytz
import time
import os

# Configuração
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"
LEAGUE_IDS = [12321]  # Champions League (adicione mais se quiser)
ARQUIVO_ENVIADOS = "pre_jogos_enviados.txt"

bot = Bot(token=BOT_TOKEN)

# Salva IDs dos jogos já enviados
def carregar_enviados():
    if os.path.exists(ARQUIVO_ENVIADOS):
        with open(ARQUIVO_ENVIADOS, "r") as f:
            return set(line.strip() for line in f)
    return set()

def salvar_enviado(jogo_id):
    with open(ARQUIVO_ENVIADOS, "a") as f:
        f.write(f"{jogo_id}\n")

# Busca jogos do dia
def buscar_jogos(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        return res.json().get("data", [])
    except Exception as e:
        print(f"Erro na liga {league_id}: {e}")
        return []

# Monta mensagem de pré-jogo
def formatar_jogo(jogo):
    home = jogo.get("home_name", "Time A")
    away = jogo.get("away_name", "Time B")
    liga = jogo.get("league_name", "Liga")
    fase = jogo.get("stage_name", "-")
    status = jogo.get("status", "-").upper()

    # Estatísticas pré-jogo
    forma_home = jogo.get("home_form", "Indisponível")
    forma_away = jogo.get("away_form", "Indisponível")
    gols_home = jogo.get("home_goals_avg", "Indisponível")
    gols_away = jogo.get("away_goals_avg", "Indisponível")
    sofridos_home = jogo.get("home_goals_conceded_avg", "Indisponível")
    sofridos_away = jogo.get("away_goals_conceded_avg", "Indisponível")

    # Data e hora
    timestamp = jogo.get("date_unix", 0)
    try:
        zona = pytz.timezone("America/Sao_Paulo")
        dt = datetime.utcfromtimestamp(timestamp).astimezone(zona)
        data = dt.strftime("%d/%m")
        hora = dt.strftime("%H:%M")
    except:
        data, hora = "?", "?"

    return (
        f"⚽ *{home} x {away}*\n"
        f"🏆 Liga: {liga} | 🏁 Fase: {fase}\n"
        f"📅 Data: {data} | ⏰ Horário: {hora}\n"
        f"📌 Status: {status}\n\n"
        f"📊 *Estatísticas pré-jogo:*\n"
        f"- Forma {home}: {forma_home}\n"
        f"- Forma {away}: {forma_away}\n"
        f"- Gols marcados (média): {home}: {gols_home} | {away}: {gols_away}\n"
        f"- Gols sofridos (média): {home}: {sofridos_home} | {away}: {sofridos_away}"
    )

# Executa verificação
def verificar_pre_jogos():
    enviados = carregar_enviados()
    novos = 0

    try:
        bot.send_message(chat_id=CHAT_ID, text="🔎 Verificando *jogos do dia*...", parse_mode="Markdown")
    except:
        pass

    hoje = datetime.now(pytz.timezone("America/Sao_Paulo")).date()

    for league_id in LEAGUE_IDS:
        jogos = buscar_jogos(league_id)
        for jogo in jogos:
            jogo_id = str(jogo.get("id"))
            status = jogo.get("status", "").lower()
            timestamp = jogo.get("date_unix", 0)
            data_jogo = datetime.utcfromtimestamp(timestamp).astimezone(pytz.timezone("America/Sao_Paulo")).date()

            if status != "notstarted" or jogo_id in enviados or data_jogo != hoje:
                continue

            try:
                mensagem = formatar_jogo(jogo)
                bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
                salvar_enviado(jogo_id)
                novos += 1
                time.sleep(2)
            except Exception as e:
                print(f"Erro ao enviar jogo {jogo_id}: {e}")
                time.sleep(5)

    if novos == 0:
        try:
            bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhum jogo novo encontrado hoje com status *NOTSTARTED*.", parse_mode="Markdown")
        except:
            pass

# Loop principal
if __name__ == "__main__":
    while True:
        verificar_pre_jogos()
        time.sleep(21600)  # Verifica a cada 6h
