import requests
from telegram import Bot

API_KEY = "6810ea1e7c44dab18f4fc039b73e8dd2"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"

headers = {"x-apisports-key": API_KEY}
url = "https://v3.football.api-sports.io/status"

res = requests.get(url, headers=headers)
dados = res.json()

plano = dados["response"]["subscription"]["plan"]
ligas_liberadas = dados["response"]["subscription"]["features"]["leagues"]
limite_dia = dados["response"]["requests"]["limit_day"]
usado_hoje = dados["response"]["requests"]["current"]

mensagem = (
    f"✅ *Status da API-Football:*\n\n"
    f"📦 Plano: *{plano}*\n"
    f"⚽ Acesso a ligas: *{'SIM' if ligas_liberadas else 'NÃO'}*\n"
    f"📊 Requisições hoje: *{usado_hoje}/{limite_dia}*"
)

bot = Bot(token=BOT_TOKEN)
bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
