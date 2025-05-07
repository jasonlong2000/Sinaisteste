import requests
from datetime import datetime
from telegram import Bot
import time

# Suas credenciais
API_KEY = "6810ea1e7c44dab18f4fc039b73e8dd2"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"

bot = Bot(token=BOT_TOKEN)

def buscar_ligas_do_dia():
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

def enviar_ligas_unicas():
    jogos = buscar_ligas_do_dia()
    ligas = set()

    for jogo in jogos:
        league = jogo["league"]
        nome = league["name"]
        pais = league["country"]
        liga_id = league["id"]
        entrada = f"{pais} - {nome} (ID: {liga_id})"
        ligas.add(entrada)

    if not ligas:
        bot.send_message(chat_id=CHAT_ID, text="⚠️ Nenhuma liga encontrada hoje na API.")
        return

    lista_formatada = "\n".join(sorted(ligas))
    mensagem = f"📋 *Ligas encontradas hoje:*\n\n{lista_formatada}"

    try:
        bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
    except Exception as e:
        print(f"Erro ao enviar mensagem no Telegram: {e}")

if __name__ == "__main__":
    enviar_ligas_unicas()
