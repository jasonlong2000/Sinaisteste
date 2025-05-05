import os
import requests
import datetime
from telegram import Bot

# Configurações do bot e da API
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FOOTYSTATS_API_KEY = os.getenv("FOOTYSTATS_API_KEY")

# Lista de ligas (será substituída dinamicamente)
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "2012,2027,2015,2030,2016,2031,2013,2032,2014,2033,2022,2023,2026,2034,2035,2036,2037,2038,2039,2040").split(",")

bot = Bot(token=BOT_TOKEN)

def send_telegram_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

def buscar_jogos_hoje():
    hoje = datetime.datetime.now().strftime("%Y-%m-%d")
    jogos_encontrados = 0
    for league_id in LEAGUE_IDS:
        url = f"https://api.football-data-api.com/league-matches?key={FOOTYSTATS_API_KEY}&league_id={league_id}&date_from={hoje}&date_to={hoje}"
        try:
            response = requests.get(url)
            data = response.json()
            if data.get("success") and isinstance(data.get("data"), list):
                jogos = data["data"]
                if not jogos:
                    send_telegram_message(f"⚽ Liga {league_id}: 0 jogos encontrados")
                    continue

                for jogo in jogos:
                    home = jogo.get("homeTeam", "Time A")
                    away = jogo.get("awayTeam", "Time B")
                    status = jogo.get("status", "-")
                    minuto = jogo.get("minute", "-")
                    msg = f"\U0001F3D0 {home} x {away}\nStatus: {status.upper()} | Minuto: {minuto}"
                    send_telegram_message(msg)
                    jogos_encontrados += 1
            else:
                print(f"[!] Liga {league_id} sem sucesso na resposta: {data}")
        except Exception as e:
            print(f"Erro ao buscar jogos da liga {league_id}: {e}")

    if jogos_encontrados == 0:
        send_telegram_message("\u26a0\ufe0f Nenhuma partida ativa ou agendada nas ligas selecionadas.")

if __name__ == "__main__":
    send_telegram_message("\U0001F680 Bot iniciado com sucesso e buscando jogos de hoje...")
    buscar_jogos_hoje()
