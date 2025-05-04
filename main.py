import os
import asyncio
import aiohttp
from flask import Flask
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time

# Variáveis de ambiente para credenciais e configurações
FOOTYSTATS_API_KEY = os.getenv('FOOTYSTATS_API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
LEAGUE_IDS = os.getenv('LEAGUE_IDS')

# Certifique-se de que as variáveis necessárias estão definidas
if not FOOTYSTATS_API_KEY or not BOT_TOKEN or not CHAT_ID or not LEAGUE_IDS:
    raise RuntimeError("Algumas variáveis de ambiente não foram definidas corretamente.")

# Preparar lista de IDs de ligas (season IDs) a monitorar
league_ids = [lid.strip() for lid in LEAGUE_IDS.split(',') if lid.strip()]

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running"

async def fetch_team_stats(session, league_id):
    """Busca estatísticas dos times de uma liga (temporada) usando a API FootyStats."""
    url = f"https://api.football-data-api.com/league-teams?key={FOOTYSTATS_API_KEY}&season_id={league_id}&include=stats"
    async with session.get(url) as response:
        return await response.json()

async def fetch_todays_matches(session, timezone='America/Sao_Paulo'):
    """Busca partidas do dia atual (hoje) na API FootyStats, filtrando por timezone."""
    today_str = datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d")
    url = f"https://api.football-data-api.com/todays-matches?key={FOOTYSTATS_API_KEY}&date={today_str}&timezone={timezone}"
    async with session.get(url) as response:
        return await response.json()

def evaluate_match_criteria(match, team_stats_map):
    """Avalia os critérios de alerta (gols, escanteios, cartões) para uma partida específica."""
    alerts = []
    home_id = match.get('homeID')
    away_id = match.get('awayID')
    home_name = match.get('homeTeam')
    away_name = match.get('awayTeam')
    # Obter estatísticas pré-carregadas dos times (médias da temporada atual)
    home_stats = team_stats_map.get(home_id, {}).get('stats', {})
    away_stats = team_stats_map.get(away_id, {}).get('stats', {})
    # Extrair médias relevantes (gols marcados, escanteios, cartões)
    avg_goals_home = home_stats.get('seasonScoredAVG_overall') or home_stats.get('seasonAVG_overall')
    avg_goals_away = away_stats.get('seasonScoredAVG_overall') or away_stats.get('seasonAVG_overall')
    avg_corners_home = home_stats.get('cornersTotalAVG_overall') or home_stats.get('cornersAVG_overall')
    avg_corners_away = away_stats.get('cornersTotalAVG_overall') or away_stats.get('cornersAVG_overall')
    avg_cards_home = home_stats.get('cardsAVG_overall')
    avg_cards_away = away_stats.get('cardsAVG_overall')
    # Verificar critérios de alerta
    if avg_goals_home and avg_goals_away and avg_goals_home >= 1.5 and avg_goals_away >= 1.5:
        alerts.append(f"⚽ Over 1.5 em {home_name} vs {away_name}")
    if avg_corners_home and avg_corners_away and (avg_corners_home + avg_corners_away) > 9:
        alerts.append(f"🏳️ Escanteios em {home_name} vs {away_name}")
    if avg_cards_home and avg_cards_away and (avg_cards_home + avg_cards_away) > 4:
        alerts.append(f"🟨 Cartões em {home_name} vs {away_name}")
    return alerts

async def run_analysis():
    """Executa a análise pré-jogo e envia mensagens de alerta para o Telegram."""
    async with aiohttp.ClientSession() as session:
        # Envia mensagem de ativação às 8h
        activation_msg = "🚨 Bot de análise pré-jogo ativado. Verificando oportunidades..."
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        await session.post(telegram_url, json={"chat_id": CHAT_ID, "text": activation_msg})
        # Busca estatísticas de todos os times nas ligas configuradas
        team_stats_map = {}
        tasks = [fetch_team_stats(session, lid) for lid in league_ids]
        results = await asyncio.gather(*tasks)
        for league_data in results:
            teams = league_data.get('data', [])
            for team in teams:
                team_id = team.get('id')
                if team_id:
                    stats = team.get('stats')
                    if isinstance(stats, list):
                        team['stats'] = stats[0] if stats else {}
                    team_stats_map[team_id] = team
        # Busca partidas de hoje e filtra próximas 12 horas
        matches_data = await fetch_todays_matches(session)
        matches = matches_data.get('data', [])
        now = datetime.now(ZoneInfo("America/Sao_Paulo"))
        cutoff = now + timedelta(hours=12)
        alerts = []
        for match in matches:
            # Filtrar partidas das ligas desejadas (competition_id corresponde ao season_id da liga)
            comp_id = match.get('competition_id')
            if comp_id and str(comp_id) not in league_ids:
                continue
            # Converter horário da partida para BRT e verificar se está dentro das próximas 12h
            timestamp = match.get('date_unix')
            if not timestamp:
                continue
            match_time = datetime.fromtimestamp(timestamp, ZoneInfo("UTC")).astimezone(ZoneInfo("America/Sao_Paulo"))
            if now <= match_time <= cutoff:
                alerts.extend(evaluate_match_criteria(match, team_stats_map))
        # Enviar alertas gerados para o Telegram
        for alert_text in alerts:
            await session.post(telegram_url, json={"chat_id": CHAT_ID, "text": alert_text})

# Loop de agendamento para rodar a análise diariamente às 8h (horário de Brasília)
def schedule_daily_run():
    tz = ZoneInfo("America/Sao_Paulo")
    while True:
        now = datetime.now(tz)
        # Próxima ocorrência de 8:00 (hoje ou amanhã)
        target_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= target_time:
            target_time += timedelta(days=1)
        # Dormir até a próxima execução
        sleep_seconds = (target_time - now).total_seconds()
        time.sleep(sleep_seconds)
        # Executar a análise pré-jogo agendada
        asyncio.run(run_analysis())

# Iniciar o agendador em segundo plano
import threading
thread = threading.Thread(target=schedule_daily_run, daemon=True)
thread.start()

# Executar o servidor Flask (mantém o serviço ativo no Render)
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
