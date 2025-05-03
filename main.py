import os
import threading
import asyncio
import aiohttp
from flask import Flask

# Configurações a partir de variáveis de ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTYSTATS_API_KEY")
LEAGUE_IDS = os.getenv("LEAGUE_IDS")  # Ex: "2012, 2015, 2019" (IDs das ligas a monitorar)

# Verifica se as variáveis essenciais estão presentes
if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise RuntimeError("BOT_TOKEN, CHAT_ID e FOOTYSTATS_API_KEY precisam estar configurados.")

# Prepara lista de IDs de ligas para consultar
league_ids = []
if LEAGUE_IDS:
    league_ids = [lid.strip() for lid in LEAGUE_IDS.split(",") if lid.strip()]
# Se nenhuma liga especificada, poderia definir uma padrão (depende do plano FootyStats do usuário)
if not league_ids:
    # Exemplo: usar Premier League como padrão (apenas para ilustrar; em produção configure LEAGUE_IDS)
    league_ids = ["2012"]  

# Monta URLs da API FootyStats para cada liga (endpoint de partidas da liga)
BASE_URL = "https://api.football-data-api.com"
league_urls = [f"{BASE_URL}/league-matches?key={API_KEY}&league_id={lid}" for lid in league_ids]

# Instancia o app Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "Seu serviço está ativo! ✅"

async def send_telegram_message(session, text: str):
    """Envia uma mensagem de texto para o Telegram usando o bot."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": text}
        # Chamada GET assíncrona para a API do Telegram
        await session.get(url, params=params)
    except Exception as e:
        print(f"[ERRO] Falha ao enviar mensagem: {e}")

async def fetch_matches(session) -> list:
    """Busca os dados de partidas ao vivo da FootyStats para as ligas configuradas."""
    all_matches = []
    for url in league_urls:
        try:
            async with session.get(url) as resp:
                data = await resp.json()
        except Exception as e:
            print(f"[ERRO] Falha ao obter dados da URL {url}: {e}")
            data = None
        if data and "data" in data:
            # Acumula partidas retornadas (cada liga retorna uma lista de partidas)
            all_matches.extend(data["data"])
        elif data and "error" in data:
            # Log de erro da API (ex: chave inválida ou limite excedido)
            print(f"[ERRO] API FootyStats retornou erro: {data.get('error')}")
    return all_matches

async def process_and_send_signals(session, matches: list):
    """Processa a lista de partidas e envia sinais ao Telegram conforme os critérios."""
    for match in matches:
        status = match.get("status", "").lower()
        if status not in ("inplay", "playing"):  # Considera apenas partidas em andamento
            continue

        # Extrai informações relevantes da partida
        home_team = match.get("homeTeam", "Time da Casa")
        away_team = match.get("awayTeam", "Time Visitante")
        minute = match.get("minute", 0) or match.get("mins", 0) or 0

        # Gols marcados
        home_goals = match.get("homeGoalCount", match.get("homeGoalcount", match.get("homeGoals", 0)))
        away_goals = match.get("awayGoalCount", match.get("awayGoalcount", match.get("awayGoals", 0)))
        try:
            home_goals = int(home_goals)
            away_goals = int(away_goals)
        except:
            home_goals = home_goals or 0
            away_goals = away_goals or 0
        total_goals = home_goals + away_goals

        # Cartões (amarelos + vermelhos)
        yellow_cards = match.get("yellowCards", match.get("yellow_cards", 0)) or 0
        red_cards = match.get("redCards", match.get("red_cards", 0)) or 0
        try:
            total_cards = int(yellow_cards) + int(red_cards)
        except:
            total_cards = 0

        # Escanteios (cantos)
        # Alguns campos possíveis: cornerCount, homeCorners/awayCorners
        corner_count = match.get("cornerCount", match.get("corner_count", 0))
        if not corner_count:
            home_corners = match.get("homeCorners", match.get("homeCornerCount", 0)) or 0
            away_corners = match.get("awayCorners", match.get("awayCornerCount", 0)) or 0
            try:
                corner_count = int(home_corners) + int(away_corners)
            except:
                corner_count = 0
        else:
            try:
                corner_count = int(corner_count)
            except:
                corner_count = 0

        # *** Critérios de Sinais ao Vivo ***

        # 1. Over 0.5 HT: Jogo sem gols próximo do intervalo (ex: >=30 min, 0x0)
        if 30 <= minute < 45 and total_goals == 0:
            msg = f"⚽ Possível Over 0.5 HT em {home_team} vs {away_team} (0x0 aos {minute} minutos)"
            await send_telegram_message(session, msg)

        # 2. Over 1.5 FT: Jogo de poucos gols no 2º tempo (ex: após 60 min com menos de 2 gols no total)
        if minute >= 60 and total_goals < 2:
            msg = f"⚽ Possível Over 1.5 FT em {home_team} vs {away_team} ({home_goals}x{away_goals} aos {minute} min)"
            await send_telegram_message(session, msg)

        # 3. Cartões: Jogo muito faltoso (ex: 5 ou mais cartões antes de 60')
        if minute <= 60 and total_cards >= 5:
            msg = f"🟨 Alerta de cartões em {home_team} vs {away_team} ({total_cards} cartões até {minute}' )"
            await send_telegram_message(session, msg)

        # 4. Escanteios: Muitos escanteios no primeiro tempo (ex: 8+ escanteios antes do intervalo)
        if minute <= 45 and corner_count >= 8:
            msg = f"🏳️‍️ Alerta de escanteios em {home_team} vs {away_team} ({corner_count} escanteios até {minute}' )"
            await send_telegram_message(session, msg)

async def main_loop_async():
    """Loop assíncrono principal que busca dados e envia sinais periodicamente."""
    async with aiohttp.ClientSession() as session:
        # Mensagem de ativação ao iniciar
        await send_telegram_message(session, "🚀 Bot ativado e acompanhando jogos ao vivo!")
        # Loop contínuo para verificar os jogos periodicamente
        while True:
            matches = await fetch_matches(session)
            if matches:
                await process_and_send_signals(session, matches)
            # Aguarda alguns segundos antes da próxima verificação (pode ajustar conforme necessidade)
            await asyncio.sleep(60)  # verifica a cada 60 segundos

def start_background_loop():
    """Inicia o loop assíncrono em uma thread separada."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_loop_async())
    except Exception as e:
        print(f"[ERRO] Loop de background encerrou: {e}")

# Inicia a thread de background antes de subir o servidor Flask
thread = threading.Thread(target=start_background_loop, daemon=True)
thread.start()

# Inicia o servidor Flask (necessário para manter o serviço ativo no Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
