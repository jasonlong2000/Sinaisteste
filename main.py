import os
import asyncio
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Verificação simples das variáveis
if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("BOT_TOKEN e CHAT_ID precisam estar definidos.")

bot = Bot(token=BOT_TOKEN)

async def teste_envio():
    try:
        await bot.send_message(chat_id=CHAT_ID, text="✅ Bot funcionando e enviando mensagens com sucesso!")
        print("Mensagem enviada!")
    except Exception as e:
        print("Erro ao enviar:", e)

asyncio.run(teste_envio())
