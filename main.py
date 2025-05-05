import requests
import asyncio
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

# Telegram and FootyStats configuration
BOT_TOKEN = '7430245294:AAGrVA6dHvM3JsYhPTXQzFmWJuJS2blam80'
CHAT_ID = '-1002675165012'
FOOTYSTATS_API_KEY = '178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9'

# Broad list of league season IDs (around 50 leagues, as provided earlier)
LEAGUE_IDS = [
    13973, 12529, 12321, 12325, 12451, 12446, 12316, 12337, 12530, 12137,
    12472, 12478, 14231, 14305, 5220, 14086, 495, 13857, 13863, 12157,
    14106, 855, 12327, 13624, 12473, 14210, 11084, 1410, 9128, 13734,
    13356, 14481, 12036, 1654, 12535, 13878, 12076, 14175, 12053, 2344,
    12101, 13678, 2426, 11500, 13887, 12278, 9981, 9816
]

# Optional mapping of league season ID to league name (for message formatting)
league_name_map = {
    13973: "USA MLS",
    12529: "Germany Bundesliga",
    12321: "Europe UEFA Champions League",
    12325: "England Premier League",
    12451: "England Championship",
    12446: "England EFL League One",
    12316: "Spain La Liga",
    12337: "France Ligue 1",
    12530: "Italy Serie A",
    12137: "Belgium Pro League",
    12472: "Austria Bundesliga",
    12478: "Austria 2. Liga",
    14231: "Brazil Serie A",
    14305: "Brazil Serie B",
    5220: "Argentina Primera División",
    14086: "Colombia Categoria Primera A",
    495: "Chile Primera División",
    13857: "Brazil Paulista A1",
    13863: "Bulgaria First League",
    12157: "Bulgaria Second League",
    14106: "Ecuador Serie A",
    855: "Uruguay Primera División",
    12327: "Europe UEFA Europa League",
    13624: "Spain Copa del Rey",
    12473: "England League Cup",
    14210: "Brazil Copa do Brasil",
    11084: "International UEFA Euro Championship",
    1410: "International FIFA Confederations Cup",
    9128: "International UEFA Euro Qualifiers",
    13734: "International UEFA Nations League",
    13356: "Asia AFC Champions League",
    14481: "Japan Emperor Cup",
    12036: "England Community Shield",
    1654: "Argentina Copa Argentina",
    12535: "Spain Supercopa de Espana",
    13878: "International FIFA Club World Cup",
    12076: "International Copa America",
    14175: "International Africa Cup of Nations",
    12053: "Europe UEFA Super Cup",
    2344: "Asia Premier League Asia Trophy",
    12101: "Belgium Belgian Super Cup",
    13678: "Italy Supercoppa Italiana",
    2426: "France Coupe de la Ligue",
    11500: "International Olympics",
    13887: "Brazil Supercopa do Brasil",
    12278: "Europe UEFA Europa Conference League",
    9981: "Mexico Campeón de Campeones",
    9816: "England Premier League Summer Series"
}

# Cache for team stats per league to avoid repeated API calls within a single analysis
teams_stats_cache = {}

# Timezone for scheduling analysis and displaying times (set to Sao Paulo as example)
LOCAL_TZ = ZoneInfo("America/Sao_Paulo")

def send_telegram_message(text: str):
    """Send a text message to the configured Telegram chat."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # Using Markdown for formatting bold text and emojis (Telegram Bot API)
    params = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.get(url, params=params, timeout=10)
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

def fetch_team_stats_for_league(season_id: int):
    """Fetch and cache team stats for a given league season (if not already cached)."""
    if season_id in teams_stats_cache:
        return
    # Only fetch if the league season is in our configured list
    if season_id not in LEAGUE_IDS:
        return
    try:
        resp = requests.get(
            f"https://api.football-data-api.com/league-teams?key={FOOTYSTATS_API_KEY}&season_id={season_id}&include=stats",
            timeout=15
        )
        data = resp.json()
        teams_data = data.get("data", [])
    except Exception as e:
        print(f"Error fetching team stats for league {season_id}: {e}")
        teams_data = []
    # Build a dictionary of team stats for quick lookup
    league_stats = {}
    for team in teams_data:
        team_id = team.get("id")
        stats = team.get("stats", {})
        if team_id is not None:
            league_stats[team_id] = stats
    teams_stats_cache[season_id] = league_stats

def analyze_and_send():
    """Fetch upcoming matches and analyze them against criteria, sending Telegram alerts if needed."""
    try:
        # Fetch today's matches from FootyStats API (for leagues selected in account)
        resp = requests.get(
            f"https://api.football-data-api.com/todays-matches?key={FOOTYSTATS_API_KEY}",
            timeout=15
        )
        data = resp.json()
        matches = data.get("data", [])
    except Exception as e:
        print(f"Error fetching matches data: {e}")
        matches = []
    if not matches:
        # If we couldn't fetch any matches (or none scheduled), just send "no signals" message
        send_telegram_message("⏱️ Análise executada. Nenhum jogo com critérios encontrados.")
        return

    # Current time (for filtering upcoming matches)
    now_ts = datetime.now(ZoneInfo("UTC")).timestamp()

    # Lists to hold alert lines for each criterion
    over15_list = []
    cards_list = []
    corners_list = []

    for match in matches:
        # Only consider matches that haven't started (pre-game)
        status = match.get("status", "").lower()
        match_time_ts = match.get("date_unix")
        if status == "complete" or status == "completed":
            continue  # already finished
        if match_time_ts is None:
            continue
        # If match time is in the past or very close to now, skip (not pre-game)
        if match_time_ts <= now_ts:
            continue

        # Identify league (season) and team IDs
        season_id = match.get("competition_id")
        home_team_id = match.get("homeID")
        away_team_id = match.get("awayID")
        home_name = match.get("home_name")
        away_name = match.get("away_name")

        if not season_id or not home_team_id or not away_team_id:
            continue

        # Fetch team stats for this league if not already cached
        fetch_team_stats_for_league(season_id)
        if season_id not in teams_stats_cache:
            continue  # if still not available, skip analysis for this match

        league_stats = teams_stats_cache[season_id]
        # Get stats for both teams
        home_stats = league_stats.get(home_team_id)
        away_stats = league_stats.get(away_team_id)
        if not home_stats or not away_stats:
            continue

        # Check criteria:
        # 1. Over 1.5 goals: both teams are offensively strong (high percentage of games over 1.5 goals)
        try:
            home_over15 = home_stats.get("seasonOver15Percentage_overall", 0)
            away_over15 = away_stats.get("seasonOver15Percentage_overall", 0)
        except:
            home_over15 = home_stats.get("seasonOver15Percentage_overall") or 0
            away_over15 = away_stats.get("seasonOver15Percentage_overall") or 0
        if isinstance(home_over15, str):
            # sometimes percentage might come as string, convert if needed
            try:
                home_over15 = float(home_over15)
            except:
                home_over15 = 0
        if isinstance(away_over15, str):
            try:
                away_over15 = float(away_over15)
            except:
                away_over15 = 0
        if home_over15 >= 80 and away_over15 >= 80:
            # Format match info
            match_time = datetime.fromtimestamp(match_time_ts, LOCAL_TZ)
            time_str = match_time.strftime("%H:%M")
            league_name = league_name_map.get(season_id, "Liga")
            over15_list.append(f"- {home_name} vs {away_name} ({league_name}) {time_str}")

        # 2. High cards: both teams have high average cards per game
        try:
            home_cards_avg = home_stats.get("cardsAVG_overall", 0)
            away_cards_avg = away_stats.get("cardsAVG_overall", 0)
        except:
            home_cards_avg = home_stats.get("cardsAVG_overall") or 0
            away_cards_avg = away_stats.get("cardsAVG_overall") or 0
        if isinstance(home_cards_avg, str):
            try:
                home_cards_avg = float(home_cards_avg)
            except:
                home_cards_avg = 0
        if isinstance(away_cards_avg, str):
            try:
                away_cards_avg = float(away_cards_avg)
            except:
                away_cards_avg = 0
        if home_cards_avg >= 2.5 and away_cards_avg >= 2.5:
            match_time = datetime.fromtimestamp(match_time_ts, LOCAL_TZ)
            time_str = match_time.strftime("%H:%M")
            league_name = league_name_map.get(season_id, "Liga")
            cards_list.append(f"- {home_name} vs {away_name} ({league_name}) {time_str}")

        # 3. High corners: both teams have high average corners per game
        try:
            home_corners_avg = home_stats.get("cornersAVG_overall", 0)
            away_corners_avg = away_stats.get("cornersAVG_overall", 0)
        except:
            home_corners_avg = home_stats.get("cornersAVG_overall") or 0
            away_corners_avg = away_stats.get("cornersAVG_overall") or 0
        if isinstance(home_corners_avg, str):
            try:
                home_corners_avg = float(home_corners_avg)
            except:
                home_corners_avg = 0
        if isinstance(away_corners_avg, str):
            try:
                away_corners_avg = float(away_corners_avg)
            except:
                away_corners_avg = 0
        if home_corners_avg >= 5.0 and away_corners_avg >= 5.0:
            match_time = datetime.fromtimestamp(match_time_ts, LOCAL_TZ)
            time_str = match_time.strftime("%H:%M")
            league_name = league_name_map.get(season_id, "Liga")
            corners_list.append(f"- {home_name} vs {away_name} ({league_name}) {time_str}")

    # Prepare Telegram alert message
    if not over15_list and not cards_list and not corners_list:
        # No criteria matched any upcoming games
        send_telegram_message("⏱️ Análise executada. Nenhum jogo com critérios encontrados.")
    else:
        message_lines = []
        if over15_list:
            message_lines.append("⚽ *Over 1.5*\n" + "\n".join(over15_list))
        if cards_list:
            message_lines.append("🟨 *Cartões*\n" + "\n".join(cards_list))
        if corners_list:
            message_lines.append("🚩 *Escanteios*\n" + "\n".join(corners_list))
        alert_message = "\n\n".join(message_lines)
        send_telegram_message(alert_message)

# Flask web server to keep the app alive on Render
from flask import Flask, request
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return "Bot is running!", 200

# Start the periodic analysis in the background
async def schedule_analysis():
    # Immediately perform an analysis on startup
    try:
        analyze_and_send()
    except Exception as e:
        print(f"Analysis error on startup: {e}")
    # Then run every 6 hours thereafter
    while True:
        try:
            await asyncio.sleep(6 * 60 * 60)  # 6 hours in seconds
            analyze_and_send()
        except Exception as e:
            print(f"Scheduled analysis error: {e}")

# Launch the background task using asyncio in a separate thread
def start_scheduler():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(schedule_analysis())

scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
scheduler_thread.start()

# Send a startup message to Telegram
send_telegram_message("🚀 Bot de análise pré-jogo rodando automaticamente a cada 6 horas!")

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
