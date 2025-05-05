import os
import asyncio
import aiohttp
from datetime import datetime
from telegram import Bot
from telegram.error import RetryAfter, TimedOut

# === Configurações ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS", "2012").split(",")

bot = Bot(token=BOT_TOKEN)

async def send_message_safe(text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await bot.send_message(chat_id=CHAT_ID, text=text)
    except TimedOut:
        print("[ERRO] Timeout no envio ao Telegram. Ignorando...")
    except Exception as e:
        print(f"[ERRO] Falha ao enviar mensagem: {e}")

async def buscar_jogos():
    await send_message_safe("🚀 Bot iniciado!\n📅 Buscando jogos das ligas configuradas...")

    url_base = "https://api.football-data-api.com/league-matches"
    headers = {"Accept": "application/json"}
    params_comuns = {
        "key": API_KEY,
        "date_from": datetime.now().strftime("%Y-%m-%d"),
        "date_to": datetime.now().strftime("%Y-%m-%d")
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        jogos_encontrados = False

        for league_id in LEAGUE_IDS:
            try:
                params = {**params_comuns, "league_id": league_id.strip()}
                async with session.get(url_base, headers=headers, params=params) as resp:
                    data = await resp.json()

                if data.get("success") and data.get("data"):
                    for match in data["data"]:
                        time_a = match.get("homeTeam", "Time A")
                        time_b = match.get("awayTeam", "Time B")
                        horario = match.get("match_start")
                        status = match.get("status", "-")

                        msg = f"\ud83c\udf1f {time_a} x {time_b}\nStatus: {status} | Início: {horario}"
                        await send_message_safe(msg)
                        await asyncio.sleep(1)  # evitar flood
                    jogos_encontrados = True
                else:
                    await send_message_safe(f"⚠️ Liga {league_id.strip()}: Nenhum jogo encontrado ou erro na API")
            except Exception as e:
                print(f"[ERRO] Erro na liga {league_id}: {e}")
                await send_message_safe(f"⚠️ Liga {league_id.strip()}: Erro inesperado ao buscar jogos")

        if not jogos_encontrados:
            await send_message_safe("⚠️ Nenhum jogo agendado para hoje nas ligas selecionadas.")

if __name__ == "__main__":
    asyncio.run(buscar_jogos())
