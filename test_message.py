import requests
from telegram import Bot

API_KEY = "6810ea1e7c44dab18f4fc039b73e8dd2"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"

HEADERS = {"x-apisports-key": API_KEY}

# Exemplo: Flamengo (time ID 2266), Copa Libertadores (13), temporada 2024
url = "https://v3.football.api-sports.io/teams/statistics?league=13&season=2024&team=2266"

res = requests.get(url, headers=HEADERS)
dados = res.json()

bot = Bot(token=BOT_TOKEN)

if "response" in dados and dados["response"]:
    corners = dados["response"].get("corners", None)

    if corners:
        media = corners.get("average", {}).get("total", "N/A")
        total = corners.get("total", {}).get("total", "N/A")

        mensagem = (
            f"🚩 *Dados de Escanteios Encontrados*\n\n"
            f"Média por jogo: *{media}*\n"
            f"Total na temporada: *{total}*"
        )
    else:
        mensagem = "⚠️ Sua API não está retornando dados de escanteios para esse time/temporada."
else:
    mensagem = "❌ Erro ao acessar a API ou time/liga/temporada inválidos."

bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
