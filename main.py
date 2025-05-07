import requests
from datetime import datetime
from telegram import Bot
import time
import os

# Configurações da API e Telegram
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"
LEAGUE_IDS = [12321]  # Champions League
ARQUIVO_ENVIADOS = "sinais_ao_vivo.txt"

bot = Bot(token=BOT_TOKEN)

# Carregar IDs já enviados
def carregar_enviados():
    if os.path.exists(ARQUIVO_ENVIADOS):
        with open(ARQUIVO_ENVIADOS, "r") as f:
            return set(line.strip() for line in f)
    return set()

# Salvar nova chave de jogo e minuto
def salvar_enviado(chave):
    with open(ARQUIVO_ENVIADOS, "a") as f:
        f.write(f"{chave}\n")

# Buscar jogos do dia para a liga
def fetch_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json().get("data", [])
    except Exception as e:
        print(f"Erro ao buscar jogos da liga {league_id}: {e}")
        return []

# Buscar detalhes da partida
def fetch_details(match_id):
    url = f"https://api.football-data-api.com/match?key={API_KEY}&match_id={match_id}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json().get("data", {})
    except Exception as e:
        print(f"Erro nos detalhes do jogo {match_id}: {e}")
        return {}

# Formatar mensagem
def formatar_mensagem(jogo, detalhes):
    home = jogo.get("home_name", "Time A")
    away = jogo.get("away_name", "Time B")
    minuto = jogo.get("minute", "-")
    liga = jogo.get("league_name", "Liga")

    # Estatísticas
    escanteios_a = detalhes.get("team_a_corners", "-")
    escanteios_b = detalhes.get("team_b_corners", "-")
    chutes_a = detalhes.get("team_a_shots", "-")
    chutes_b = detalhes.get("team_b_shots", "-")
    posse_a = detalhes.get("team_a_possession", "-")
    posse_b = detalhes.get("team_b_possession", "-")
    amarelos_a = detalhes.get("team_a_yellow_cards", "-")
    amarelos_b = detalhes.get("team_b_yellow_cards", "-")

    mensagem = (
        f"⚽ *Jogo ao vivo!*\n"
        f"🏟️ {home} x {away}\n"
        f"Liga: {liga} | ⏱️ Minuto: {minuto}\n\n"
        f"📊 *Estatísticas:*\n"
        f"- Escanteios: {home}: {escanteios_a} | {away}: {escanteios_b}\n"
        f"- Chutes: {home}: {chutes_a} | {away}: {chutes_b}\n"
        f"- Posse de bola: {home}: {posse_a}% | {away}: {posse_b}%\n"
        f"- Cartões Amarelos: {home}: {amarelos_a} | {away}: {amarelos_b}"
    )
    return mensagem

# Loop de monitoramento
def monitorar():
    enviados = carregar_enviados()
    houve_jogo = False

    print("🔄 Verificando jogos ao vivo da Champions League...")
    try:
        bot.send_message(chat_id=CHAT_ID, text="🔄 Buscando *jogos ao vivo* da Champions League...", parse_mode="Markdown")
    except Exception as e:
        print(f"Erro ao enviar mensagem de status: {e}")

    for league_id in LEAGUE_IDS:
        jogos = fetch_matches(league_id)
        for jogo in jogos:
            if jogo.get("status") != "inplay":
                continue

            jogo_id = str(jogo.get("id"))
            minuto = str(jogo.get("minute", "-"))
            chave = f"{jogo_id}_{minuto}"

            if chave in enviados:
                continue

            detalhes = fetch_details(jogo_id)
            mensagem = formatar_mensagem(jogo, detalhes)

            try:
                bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
                salvar_enviado(chave)
                enviados.add(chave)
                houve_jogo = True
                time.sleep(2)
            except Exception as e:
                print(f"Erro ao enviar jogo {jogo_id}: {e}")
                time.sleep(5)

    if not houve_jogo:
        try:
            bot.send_message(chat_id=CHAT_ID, text="❌ Nenhum *jogo ao vivo* encontrado na Champions League.", parse_mode="Markdown")
        except Exception as e:
            print(f"Erro ao enviar aviso final: {e}")

# Execução contínua a cada 5 minutos
if __name__ == "__main__":
    while True:
        monitorar()
        time.sleep(300)  # 5 minutos
