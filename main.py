import requests
import time
import os
from telegram import Bot
from datetime import datetime

API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
CHAT_ID = "-1002675165012"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
LEAGUE_IDS = [
    2003, 2004, 2005, 2006, 2007, 2008, 2012, 2013, 2014, 2015, 2016,
    2017, 2022, 2023, 2026, 2031, 2032, 2033, 2034, 2035, 2036, 2037,
    2038, 2039, 2040
]

dispatched_matches = set()
bot = Bot(token=BOT_TOKEN)


def fetch_today_matches(league_id):
    url = f"https://api.football-data-api.com/todays-matches?key={API_KEY}&league_id={league_id}"
    try:
        response = requests.get(url)
        return response.json().get("data", [])
    except Exception as e:
        print(f"Erro na liga {league_id}: {e}")
        return []


def format_match(match):
    home = match.get("home_name", "Time A")
    away = match.get("away_name", "Time B")
    status = match.get("status", "-").upper()
    minute = match.get("minute", "-")
    timestamp = match.get("date_unix", 0)
    date_str = datetime.fromtimestamp(timestamp).strftime('%d/%m') if timestamp else "?"
    hour_str = datetime.fromtimestamp(timestamp).strftime('%H:%M') if timestamp else "?"
    return f"⚽ {home} x {away}\nStatus: {status} | Minuto: {minute} | Data: {date_str} | Horário: {hour_str}"


def main():
    bot.send_message(chat_id=CHAT_ID, text="
