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

    headers = {
        "x-apisports-key": API_KEY
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json().get("response", [])

        # LISTAR NOMES EXATOS DAS LIGAS DO DIA
        print("\n🔎 LIGAS DISPONÍVEIS HOJE:")
        ligas_unicas = set()
        for jogo in data:
            liga = jogo["league"]
            chave = f"{liga['country']} - {liga['name']}"
            ligas_unicas.add(chave)
        for nome in sorted(ligas_unicas):
            print("-", nome)
        print("✔️ Fim da lista.\n")

        return data
    except Exception as e:
        print(f"Erro ao buscar jogos: {e}")
        return []

# NÃO ENVIA MENSAGEM — só busca e imprime no log
def verificar_jogos():
    _ = carregar_enviados()
    _ = buscar_jogos_do_dia()

if __name__ == "__main__":
    verificar_jogos()
