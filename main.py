import os
import time
import asyncio
import threading
import requests
from telegram import Bot
from flask import Flask

# Configurações do bot e API
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = -1002675165012
FOOTYSTATS_API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
API_URL = f"https://api.football-data-api.com/todays-matches?key={FOOTYSTATS_API_KEY}"

# Inicializa bot e Flask
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# Teste de envio manual
try:
    bot.send_message(chat_id=CHAT_ID, text="🟢 Teste manual de mensagem.")
except Exception as e:
    print("Erro ao enviar teste:", e)

@app.route("/")
def index():
    return "Bot está ativo!"

triggered = {1: set(), 2: set(), 3: set(), 4: set()}

def fetch_matches():
    try:
        response = requests.get(API_URL)
        data = response.json()
        if data.get("success"):
            return data.get("data", [])
    except Exception as e:
        print(f"Erro ao buscar dados da API: {e}")
    return []

def check_strategy1(matches):
    for match in matches:
        match_id = match.get("id")
        if match_id in triggered[1]:
            continue
        shots_a = match.get("team_a_shots")
        shots_b = match.get("team_b_shots")
        corners_a = match.get("team_a_corners")
        corners_b = match.get("team_b_corners")
        pos_a = match.get("team_a_possession")
        pos_b = match.get("team_b_possession")
        if None in (shots_a, shots_b, corners_a, corners_b, pos_a, pos_b):
            continue
        if -1 in (shots_a, shots_b, corners_a, corners_b, pos_a, pos_b):
            continue
        total_shots = shots_a + shots_b
        total_corners = corners_a + corners_b
        max_pos = max(pos_a, pos_b)
        start_time = match.get("date_unix")
        if not start_time:
            continue
        elapsed = int((time.time() - start_time) // 60)
        if 25 <= elapsed <= 45:
            if total_shots >= 6 and total_corners >= 4 and max_pos >= 60:
                home = match.get("home_name", "Casa")
                away = match.get("away_name", "Fora")
                text = f"⚽ Estratégia 1: {home} x {away}\nMin: {elapsed}' | Chutes: {total_shots} | Escanteios: {total_corners} | Posse: {max_pos}%"
                try:
                    bot.send_message(chat_id=CHAT_ID, text=text)
                    triggered[1].add(match_id)
                except Exception as e:
                    print(f"Erro Estratégia 1: {e}")

def check_strategy2(matches):
    for match in matches:
        match_id = match.get("id")
        if match_id in triggered[2]:
            continue
        shots_a = match.get("team_a_shots")
        shots
