import os
import time
import asyncio
import threading
import requests
from telegram import Bot
from flask import Flask

# Configurações do bot e API (substitua os valores de exemplo pelas suas credenciais)
BOT_TOKEN = "123456:ABCDEF_example_bot_token"
CHAT_ID = 123456789  # ID do chat ou canal do Telegram para enviar os alertas
FOOTYSTATS_API_KEY = "exemplo_footystats_api_key"

# Inicializa bot do Telegram e aplicação Flask
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# Rota básica para verificar se o servidor está ativo
@app.route("/")
def index():
    return "Bot está ativo!"

# Estruturas para rastrear quais jogos já dispararam cada estratégia (evitar duplicação de alertas)
triggered = {
    1: set(),
    2: set(),
    3: set(),
    4: set()
}

def fetch_matches():
    """Obtém os dados dos jogos de hoje da API Football Data API (FootyStats)."""
    try:
        url = f"https://api.football-data-api.com/todays-matches?key={FOOTYSTATS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        if data.get("success"):
            return data.get("data", [])
    except Exception as e:
        print(f"Erro ao buscar dados da API: {e}")
    return []

def check_strategy1(matches):
    """Estratégia 1: Over 0.5 HT."""
    for match in matches:
        match_id = match.get("id")
        if match_id in triggered[1]:
            continue
        # Recupera estatísticas necessárias
        shots_a = match.get("team_a_shots")
        shots_b = match.get("team_b_shots")
        corners_a = match.get("team_a_corners")
        corners_b = match.get("team_b_corners")
        pos_a = match.get("team_a_possession")
        pos_b = match.get("team_b_possession")
        # Verifica se as estatísticas estão disponíveis e válidas
        if None in (shots_a, shots_b, corners_a, corners_b, pos_a, pos_b):
            continue
        if shots_a == -1 or shots_b == -1 or corners_a == -1 or corners_b == -1 or pos_a == -1 or pos_b == -1:
            continue
        # Calcula métricas combinadas
        total_shots = shots_a + shots_b
        total_corners = corners_a + corners_b
        max_pos = pos_a if pos_a >= pos_b else pos_b  # maior posse de bola
        # Calcula minuto atual do jogo
        start_time = match.get("date_unix")
        if not start_time:
            continue
        current_time = time.time()
        if current_time < start_time:
            continue  # jogo ainda não iniciado
        elapsed_minutes = int((current_time - start_time) // 60)
        # Verifica condições da estratégia 1: minuto 25-45, ≥6 chutes, ≥4 escanteios, posse ≥60% para um time
        if 25 <= elapsed_minutes <= 45:
            if total_shots >= 6 and total_corners >= 4 and max_pos >= 60:
                home = match.get("home_name", "Time da Casa")
                away = match.get("away_name", "Time Visitante")
                message = f"Estratégia 1 (Over 0.5 HT) detectada no jogo {home} vs {away}!"
                try:
                    bot.send_message(chat_id=CHAT_ID, text=message)
                    triggered[1].add(match_id)
                    print(f"Alerta da Estratégia 1 enviado para o jogo {home} vs {away}.")
                except Exception as e:
                    print(f"Erro ao enviar mensagem Telegram (Estratégia 1): {e}")

def check_strategy2(matches):
    """Estratégia 2: Over 1.5 FT."""
    for match in matches:
        match_id = match.get("id")
        if match_id in triggered[2]:
            continue
        shots_a = match.get("team_a_shots")
        shots_b = match.get("team_b_shots")
        corners_a = match.get("team_a_corners")
        corners_b = match.get("team_b_corners")
        goals_home = match.get("homeGoalCount")
        goals_away = match.get("awayGoalCount")
        if None in (shots_a, shots_b, corners_a, corners_b, goals_home, goals_away):
            continue
        if shots_a == -1 or shots_b == -1 or corners_a == -1 or corners_b == -1:
            continue
        total_shots = shots_a + shots_b
        total_corners = corners_a + corners_b
        total_goals = (goals_home or 0) + (goals_away or 0)
        start_time = match.get("date_unix")
        if not start_time:
            continue
        current_time = time.time()
        if current_time < start_time:
            continue
        elapsed_minutes = int((current_time - start_time) // 60)
        # Condições da estratégia 2: minuto 50-75, placar 0-0, ≥12 chutes, ≥5 escanteios
        if 50 <= elapsed_minutes <= 75:
            if total_goals == 0 and total_shots >= 12 and total_corners >= 5:
                home = match.get("home_name", "Time da Casa")
                away = match.get("away_name", "Time Visitante")
                message = f"Estratégia 2 (Over 1.5 FT) detectada no jogo {home} vs {away}!"
                try:
                    bot.send_message(chat_id=CHAT_ID, text=message)
                    triggered[2].add(match_id)
                    print(f"Alerta da Estratégia 2 enviado para o jogo {home} vs {away}.")
                except Exception as e:
                    print(f"Erro ao enviar mensagem Telegram (Estratégia 2): {e}")

def check_strategy3(matches):
    """Estratégia 3: Cartões por Faltas."""
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
        if fouls_a == -1 or fouls_b == -1 or shots_a == -1 or shots_b == -1 or corners_a == -1 or corners_b == -1:
            continue
        total_fouls = fouls_a + fouls_b
        total_shots = shots_a + shots_b
        total_corners = corners_a + corners_b
        start_time = match.get("date_unix")
        if not start_time:
            continue
        current_time = time.time()
        if current_time < start_time:
            continue
        elapsed_minutes = int((current_time - start_time) // 60)
        # Condições da estratégia 3: a partir do minuto 80 (80-90), ≥20 faltas, ≥8 escanteios, ≥10 chutes
        if 80 <= elapsed_minutes <= 90:
            if total_fouls >= 20 and total_corners >= 8 and total_shots >= 10:
                home = match.get("home_name", "Time da Casa")
                away = match.get("away_name", "Time Visitante")
                message = f"Estratégia 3 (Cartões por Faltas) detectada no jogo {home} vs {away}!"
                try:
                    bot.send_message(chat_id=CHAT_ID, text=message)
                    triggered[3].add(match_id)
                    print(f"Alerta da Estratégia 3 enviado para o jogo {home} vs {away}.")
                except Exception as e:
                    print(f"Erro ao enviar mensagem Telegram (Estratégia 3): {e}")

def check_strategy4(matches):
    """Estratégia 4: Escanteios Prováveis."""
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
        if shots_a == -1 or shots_b == -1 or corners_a == -1 or corners_b == -1 or pos_a == -1 or pos_b == -1:
            continue
        total_shots = shots_a + shots_b
        total_corners = corners_a + corners_b
        max_pos = pos_a if pos_a >= pos_b else pos_b
        start_time = match.get("date_unix")
        if not start_time:
            continue
        current_time = time.time()
        if current_time < start_time:
            continue
        elapsed_minutes = int((current_time - start_time) // 60)
        # Condições da estratégia 4: minuto 10-75, ≥10 chutes, posse ≥60%, ≤6 escanteios
        if 10 <= elapsed_minutes <= 75:
            if total_shots >= 10 and max_pos >= 60 and total_corners <= 6:
                home = match.get("home_name", "Time da Casa")
                away = match.get("away_name", "Time Visitante")
                message = f"Estratégia 4 (Escanteios Prováveis) detectada no jogo {home} vs {away}!"
                try:
                    bot.send_message(chat_id=CHAT_ID, text=message)
                    triggered[4].add(match_id)
                    print(f"Alerta da Estratégia 4 enviado para o jogo {home} vs {away}.")
                except Exception as e:
                    print(f"Erro ao enviar mensagem Telegram (Estratégia 4): {e}")

async def main_loop():
    # Envia mensagem inicial avisando que o bot está ativo
    try:
        bot.send_message(chat_id=CHAT_ID, text="🤖 Bot de sinais esportivos está ativo!")
        print("Mensagem inicial enviada ao Telegram.")
    except Exception as e:
        print(f"Erro ao enviar mensagem inicial: {e}")
    # Loop principal que verifica as estratégias a cada 2 minutos
    while True:
        matches = fetch_matches()
        if matches:
            check_strategy1(matches)
            check_strategy2(matches)
            check_strategy3(matches)
            check_strategy4(matches)
        else:
            print("Nenhum dado de partidas disponível no momento.")
        await asyncio.sleep(120)  # espera 2 minutos até a próxima verificação

def run_flask():
    """Inicia o servidor Flask para manter o serviço ativo."""
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Inicializa o servidor Flask em uma thread separada e inicia o loop assíncrono principal
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    asyncio.run(main_loop())
