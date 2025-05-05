from telegram.error import RetryAfter
import time

def enviar_telegram(bot, texto):
    while True:
        try:
            bot.send_message(chat_id=CHAT_ID, text=texto)
            time.sleep(3)  # pausa de segurança
            break
        except RetryAfter as e:
            tempo = int(e.retry_after)
            print(f"Telegram limitou. Esperando {tempo} segundos...")
            time.sleep(tempo)
        except Exception as err:
            print(f"Erro inesperado: {err}")
            break
