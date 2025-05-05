import os
import requests
from datetime import datetime, timezone, timedelta

# Load configuration from environment
API_KEY = os.environ.get("FOOTYSTATS_API_KEY")  # FootyStats API key
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Determine today's date (Brazil timezone UTC-3 for current date)
today_date = datetime.now(timezone.utc) - timedelta(hours=3)
date_str = today_date.strftime("%Y-%m-%d")

# Fetch list of selected leagues (top 50 leagues) to map league ID to name
league_list_url = "https://api.football-data-api.com/league-list"
league_params = {"key": API_KEY, "chosen_leagues_only": "true"}
league_resp = requests.get(league_list_url, params=league_params)
leagues_data = league_resp.json().get("data", [])

league_name_map = {}
for league in leagues_data:
    # Each league entry contains a season with id and a league_name and country
    season_info = league.get("season") or {}
    league_id = season_info.get("id") or league.get("id")
    league_name = league.get("league_name") or league.get("name") or ""
    country = league.get("country") or ""
    if league_id:
        league_name_map[league_id] = (league_name, country)

# Prepare a helper for duplicate league names
league_name_counts = {}
for lid, (lname, country) in league_name_map.items():
    league_name_counts[lname] = league_name_counts.get(lname, 0) + 1

# Fetch today's matches for the selected leagues
matches_url = "https://api.football-data-api.com/todays-matches"
matches_params = {"key": API_KEY, "date": date_str}
matches_resp = requests.get(matches_url, params=matches_params)
matches = matches_resp.json().get("data", [])

# Build the message text
if not matches:
    message_text = "Nenhum jogo encontrado para hoje nas ligas selecionadas."
else:
    lines = []
    for match in matches:
        comp_id = match.get("competition_id") or match.get("league_id") or match.get("season_id")
        home_team = match.get("home_name") or match.get("homeTeam") or match.get("home")
        away_team = match.get("away_name") or match.get("awayTeam") or match.get("away")
        # Determine league display name (add country if duplicate league_name exists)
        league_name, country = league_name_map.get(comp_id, ("", ""))
        if league_name_counts.get(league_name, 0) > 1 and country:
            league_display = f"{league_name} ({country})"
        else:
            league_display = league_name
        # Convert time from UNIX timestamp to HH:MM in Brazil timezone (UTC-3)
        time_str = ""
        date_unix = match.get("date_unix") or match.get("date") or match.get("timestamp")
        if date_unix:
            # If date_unix is given in seconds
            try:
                ts = int(date_unix)
            except:
                ts = int(float(date_unix))
            dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
            dt_brt = dt_utc - timedelta(hours=3)
            time_str = dt_brt.strftime("%H:%M")
        lines.append(f"Liga: {league_display}")
        lines.append(f"Hor\u00e1rio: {time_str}")
        lines.append(f"Confronto: {home_team} x {away_team}")
        lines.append("")  # blank line separator
    # Remove the last blank line
    if lines and lines[-1] == "":
        lines.pop()
    message_text = "\n".join(lines)

# Send message to Telegram
telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(telegram_url, data={"chat_id": CHAT_ID, "text": message_text})
