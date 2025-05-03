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

@app.route("/")
def index():
    return "Bot está ativo!"

triggered = {1: set(), 2: set(), 3: set(), 4: set()}

def fetch_matches():
    print("Verificando partidas ao vivo...")
    try:
        response = requests.get(API_URL)
        data = response.json()
        if data.get("success"):
            return data.get("data", [])
    except Exception as e:
        print(f"Erro ao buscar dados da API: {e}")
    return []

def check_strategy1(matches):
    print("Executando estratégia 1...")
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
    print("Executando estratégia 2...")
    for match in matches:
        match_id = match.get("id")
        if match_id in triggered[2]:
            continue
        shots_a = match.get("team_a_shots")
        shots_b = match.get("team_b_shots")
        corners_a = match.get("team_a_corners")
        corners_b = match.get("team_b_corners")
        goals_a = match.get("homeGoalCount", 0)
        goals_b = match.get("awayGoalCount", 0)
        if None in (shots_a, shots_b, corners_a, corners_b, goals_a, goals_b):
            continue
        total_shots = shots_a + shots_b
        total_corners = corners_a + corners_b
        total_goals = goals_a + goals_b
        start_time = match.get("date_unix")
        if not start_time:
            continue
        elapsed = int((time.time() - start_time) // 60)
        if 50 <= elapsed <= 75:
            if total_goals == 0 and total_shots >= 12 and total_corners >= 5:
                home = match.get("home_name", "Casa")
                away = match.get("away_name", "Fora")
                text = f"🔥 Estratégia 2: {home} x {away}\nMin: {elapsed}' | Chutes: {total_shots} | Escanteios: {total_corners}"
                try:
                    bot.send_message(chat_id=CHAT_ID, text=text)
                    triggered[2].add(match_id)
                except Exception as e:
                    print(f"Erro Estratégia 2: {e}")

def check_strategy3(matches):
    print("Executando estratégia 3...")
    for match in matches:
        match_id = match.get("id")
        if match_id in triggered[3]:
            continue
        fouls_a = match.get("team_a_fouls")
        fouls_b = match.get("team_b_fouls")
        shots_a = match.get("team_a_shots")
        shots_b = match.get("team_b_shots")
        corners_a = match.get("team_a_corners")
        corners_b = match.get("team_b_corners")
        if None in (fouls_a, fouls_b, shots_a, shots_b, corners_a, corners_b):
            continue
        total_fouls = fouls_a + fouls_b
        total_shots = shots_a + shots_b
        total_corners = corners_a + corners_b
        start_time = match.get("date_unix")
        if not start_time:
            continue
        elapsed = int((time.time() - start_time) // 60)
        if elapsed <= 80:
            if total_fouls >= 20 and total_corners >= 8 and total_shots >= 10:
                home = match.get("home_name", "Casa")
                away = match.get("away_name", "Fora")
                text = f"🟨 Estratégia 3: {home} x {away}\nMin: {elapsed}' | Faltas: {total_fouls} | Chutes: {total_shots} | Escanteios: {total_corners}"
                try:
                    bot.send_message(chat_id=CHAT_ID, text=text)
                    triggered[3].add(match_id)
                except Exception as e:
                    print(f"Erro Estratégia 3: {e}")

def check_strategy4(matches):
    print("Executando estratégia 4...")
    for match in matches:
        match_id = match.get("id")
        if match_id in triggered[4]:
            continue
        shots_a = match.get("team_a_shots")
        shots_b = match.get("team_b_shots")
        corners_a = match.get("team_a_corners")
        corners_b = match.get("team_b_corners")
        pos_a = match.get("team_a_possession")
        pos_b = match.get("team_b_possession")
        if None in (shots_a, shots_b, corners_a, corners_b, pos_a, pos_b):
            continue
        total_shots = shots_a + shots_b
        total_corners = corners_a + corners_b
        max_pos = max(pos_a, pos_b)
        start_time = match.get("date_unix")
        if not start_time:
            continue
        elapsed = int((time.time() - start_time) // 60)
        if 10 <= elapsed <= 75:
            if total_shots >= 10 and max_pos >= 60 and total_corners <= 6:
                home = match.get("home_name", "Casa")
                away = match.get("away_name", "Fora")
                text = f"🚩 Estratégia 4: {home} x {away}\nMin: {elapsed}' | Chutes: {total_shots} | Escanteios: {total_corners} | Posse: {max_pos}%"
                try:
                    bot.send_message(chat_id=CHAT_ID, text=text)
                    triggered[4].add(match_id)
                except Exception as e:
                    print(f"Erro Estratégia 4: {e}")

async def main_loop():
    try:
        bot.send_message(chat_id=CHAT_ID, text="🤖 Bot de sinais esportivos ativado!")
    except Exception as e:
        print(f"Erro aviso inicial: {e}")
    while True:
        matches = fetch_matches()
        if matches:
            check_strategy1(matches)
            check_strategy2(matches)
            check_strategy3(matches)
            check_strategy4(matches)
        await asyncio.sleep(120)

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_loop())
