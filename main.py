import os
import requests
import time
import threading
import asyncio
from flask import Flask

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FOOTY_API_KEY = os.environ.get("FOOTY_API_KEY")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
FOOTY_API_URL = "https://api.football-data-api.com"

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot de Sinais Esportivos está rodando."

team_names_cache = {}

def get_team_name(team_id):
    if team_id in team_names_cache:
        return team_names_cache[team_id]
    try:
        url = f"{FOOTY_API_URL}/team?key={FOOTY_API_KEY}&team_id={team_id}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        team_data = data.get("data", {})
        if isinstance(team_data, list):
            team_data = team_data[0] if team_data else {}
        name = team_data.get("name") or team_data.get("full_name") or team_data.get("english_name") or str(team_id)
        name_pt = team_data.get("name_pt")
        if name_pt and name_pt.strip():
            name = name_pt
        team_names_cache[team_id] = name
        return name
    except:
        return str(team_id)

signaled_matches = {"S1": set(), "S2": set(), "S3": set(), "S4": set()}
alerted_matches = {"S1": set(), "S2": set(), "S3": set(), "S4": set()}

def send_telegram_message(text):
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Erro ao enviar mensagem Telegram: {e}")

def check_and_send_signals():
    try:
        url = f"{FOOTY_API_URL}/todays-matches?key={FOOTY_API_KEY}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
    except Exception as e:
        print(f"Erro ao consultar partidas: {e}")
        return

    if not data.get("success"):
        print("Falha na resposta da API.")
        return

    matches = data.get("data", [])
    for match in matches:
        try:
            if match.get("status") != "incomplete":
                continue
            match_id = match.get("id")
            home_goals = match.get("homeGoalCount", 0)
            away_goals = match.get("awayGoalCount", 0)
            if match.get("team_a_shots") == -1:
                continue

            current_minute = None
            if match.get("date_unix"):
                try:
                    kickoff_ts = int(match["date_unix"])
                    elapsed = time.time() - kickoff_ts
                    current_minute = min(max(0, int(elapsed // 60)), 90)
                except:
                    current_minute = None

            shots_home = max(0, match.get("team_a_shots", 0))
            shots_away = max(0, match.get("team_b_shots", 0))
            shots_on_target_home = max(0, match.get("team_a_shotsOnTarget", 0))
            shots_on_target_away = max(0, match.get("team_b_shotsOnTarget", 0))
            corners_home = max(0, match.get("team_a_corners", 0))
            corners_away = max(0, match.get("team_b_corners", 0))
            fouls_home = max(0, match.get("team_a_fouls", 0))
            fouls_away = max(0, match.get("team_b_fouls", 0))
            poss_home = max(0, match.get("team_a_possession", 0))
            poss_away = max(0, match.get("team_b_possession", 0))

            total_shots = shots_home + shots_away
            total_shots_on_target = shots_on_target_home + shots_on_target_away
            total_corners = corners_home + corners_away
            total_fouls = fouls_home + fouls_away
            max_possession = max(poss_home, poss_away)

            home_team_name = get_team_name(match.get("homeID"))
            away_team_name = get_team_name(match.get("awayID"))
            score_text = f"{home_goals}x{away_goals}"
            minute_text = f"{current_minute}'" if current_minute is not None else ""

            if current_minute is None or (25 <= current_minute <= 45):
                strat = "S1"
                if total_shots_on_target >= 6 and total_corners >= 4 and max_possession >= 60:
                    if match_id not in signaled_matches[strat]:
                        msg = f"🚨 Over 0.5 HT:\n{home_team_name} x {away_team_name} - {score_text} {minute_text}\nChutes: {total_shots_on_target}, Escanteios: {total_corners}, Posse: {poss_home}% - {poss_away}%"
                        send_telegram_message(msg)
                        signaled_matches[strat].add(match_id)
                elif total_shots_on_target >= 4 and total_corners >= 3 and max_possession >= 55:
                    if match_id not in alerted_matches[strat]:
                        msg = f"👀 Analisando (Over 0.5 HT): {home_team_name} x {away_team_name} - {minute_text}"
                        send_telegram_message(msg)
                        alerted_matches[strat].add(match_id)

            if current_minute is None or (50 <= current_minute <= 75):
                strat = "S2"
                if home_goals == 0 and away_goals == 0:
                    if total_shots >= 12 and total_corners >= 5:
                        if match_id not in signaled_matches[strat]:
                            msg = f"🚨 Over 1.5 FT:\n{home_team_name} x {away_team_name} - {score_text} {minute_text}\nChutes: {total_shots}, Escanteios: {total_corners}"
                            send_telegram_message(msg)
                            signaled_matches[strat].add(match_id)
                    elif total_shots >= 8 and total_corners >= 4:
                        if match_id not in alerted_matches[strat]:
                            msg = f"👀 Analisando (Over 1.5 FT): {home_team_name} x {away_team_name} - {minute_text}"
                            send_telegram_message(msg)
                            alerted_matches[strat].add(match_id)

            if current_minute is None or current_minute <= 80:
                strat = "S3"
                if total_fouls >= 20 and total_shots >= 10 and total_corners >= 8:
                    if match_id not in signaled_matches[strat]:
                        msg = f"🚨 Cartões:\n{home_team_name} x {away_team_name} - {minute_text}\nFaltas: {total_fouls}, Chutes: {total_shots}, Escanteios: {total_corners}"
                        send_telegram_message(msg)
                        signaled_matches[strat].add(match_id)
                elif total_fouls >= 15 and total_shots >= 7 and total_corners >= 6:
                    if match_id not in alerted_matches[strat]:
                        msg = f"👀 Analisando (Cartões): {home_team_name} x {away_team_name} - {minute_text}"
                        send_telegram_message(msg)
                        alerted_matches[strat].add(match_id)

            if current_minute is None or (10 <= current_minute <= 75):
                strat = "S4"
                if total_corners <= 6:
                    if total_shots >= 10 and max_possession >= 60:
                        if match_id not in signaled_matches[strat]:
                            msg = f"🚨 Escanteios:\n{home_team_name} x {away_team_name} - {minute_text}\nChutes: {total_shots}, Escanteios: {total_corners}, Posse: {poss_home}% - {poss_away}%"
                            send_telegram_message(msg)
                            signaled_matches[strat].add(match_id)
                    elif total_shots >= 7 and max_possession >= 55:
                        if match_id not in alerted_matches[strat]:
                            msg = f"👀 Analisando (Escanteios): {home_team_name} x {away_team_name} - {minute_text}"
                            send_telegram_message(msg)
                            alerted_matches[strat].add(match_id)
        except Exception as e:
            print(f"Erro ao processar jogo {match.get('id')}: {e}")

async def background_loop():
    send_telegram_message("✅ Bot de sinais ativado e monitorando jogos ao vivo!")
    while True:
        await asyncio.to_thread(check_and_send_signals)
        await asyncio.sleep(120)

def start_background_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(background_loop())

threading.Thread(target=start_background_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
