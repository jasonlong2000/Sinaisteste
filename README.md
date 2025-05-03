# Bot de Telegram para sinais de apostas futebolísticas
# Importando bibliotecas necessárias
import asyncio
import requests
import time
from flask import Flask
import threading
from telegram import Bot

# Configurações (Tokens, IDs, etc.)
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = -1002675165012  # ID do canal do Telegram para enviar os sinais
API_KEY = "178188b6d107c6acc99704e53d196b72c720d048a07044d16fa9334acb849dd9"
API_URL = f"https://api.football-data-api.com/todays-matches?key={API_KEY}"

# Inicializando o bot do Telegram
bot = Bot(token=BOT_TOKEN)

# Configurando o servidor Flask para manter o bot ativo (no Replit)
app = Flask(__name__)
@app.route('/')
def index():
    return "Bot is running"

# Função assíncrona para enviar mensagem usando o bot
async def send_message(text: str):
    try:
        # Envia a mensagem para o chat especificado (usa thread para não bloquear o loop)
        await asyncio.to_thread(bot.send_message, chat_id=CHAT_ID, text=text)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

# Função assíncrona para buscar os jogos e estatísticas da API
async def fetch_matches():
    try:
        # Usa requests (bloqueante) dentro de asyncio.to_thread para não travar o loop
        response = await asyncio.to_thread(requests.get, API_URL, timeout=10)
        # Verifica se a resposta foi bem-sucedida
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao obter dados da API: status code {response.status_code}")
    except Exception as e:
        print(f"Exceção ao obter dados da API: {e}")
    return None

# Função principal de execução do bot
async def main():
    # Envia uma mensagem inicial avisando que o bot foi iniciado
    await send_message("🤖 Bot iniciado com sucesso!")
    print("Bot iniciado, enviando sinais a cada 120 segundos...")

    # Estrutura de dados para evitar enviar sinais duplicados para o mesmo jogo/estratégia
    sent_signals = set()  # armazenará tuplas (match_id, strategy)

    # Loop infinito para verificar estratégias continuamente
    while True:
        data = await fetch_matches()
        if data is None:
            # Aguarda e tenta novamente se não conseguiu obter dados
            await asyncio.sleep(120)
            continue

        # Extrai a lista de partidas do dia (pode estar sob a chave 'data')
        if isinstance(data, dict):
            matches = data.get('data') or data.get('matches') or data.get('response') or data.get('results')
        elif isinstance(data, list):
            matches = data
        else:
            matches = None

        if not matches:
            # Se não há partidas retornadas, aguarda e continua
            await asyncio.sleep(120)
            continue

        current_time = time.time()
        # Itera sobre cada partida para verificar as estratégias
        for match in matches:
            try:
                match_id = match.get('id') or match.get('match_id') or match.get('fixture_id')
                status = str(match.get('status', '')).lower()
                # Ignora partidas já finalizadas
                if status in ['complete', 'completed', 'finished', 'ft']:
                    continue

                # Calcula o minuto atual da partida
                start_ts = match.get('date_unix') or match.get('timestamp') or match.get('start_timestamp')
                if start_ts is None:
                    continue
                try:
                    start_ts = float(start_ts)
                except:
                    continue
                if current_time < start_ts:
                    continue

                elapsed_minutes = int((current_time - start_ts) // 60)
                if elapsed_minutes < 0:
                    continue

                # Extrai estatísticas relevantes (com tratamento de valores faltantes)
                home_shots = match.get('team_a_shots', match.get('home_shots', 0))
                away_shots = match.get('team_b_shots', match.get('away_shots', 0))
                home_corners = match.get('team_a_corners', match.get('home_corners', 0))
                away_corners = match.get('team_b_corners', match.get('away_corners', 0))
                home_fouls = match.get('team_a_fouls', match.get('home_fouls', 0))
                away_fouls = match.get('team_b_fouls', match.get('away_fouls', 0))
                home_poss = match.get('team_a_possession', match.get('home_possession', 0))
                away_poss = match.get('team_b_possession', match.get('away_possession', 0))
                home_goals = match.get('homeGoalCount', match.get('team_a_goal_count', match.get('home_score', 0)))
                away_goals = match.get('awayGoalCount', match.get('team_b_goal_count', match.get('away_score', 0)))

                # Função auxiliar para normalizar valores numéricos (trata None e valores negativos)
                def fix_stat(value):
                    if value is None:
                        return 0
                    try:
                        val = float(value)
                    except:
                        return 0
                    if val < 0:
                        return 0
                    return int(val) if val.is_integer() else round(val, 2)

                home_shots = fix_stat(home_shots)
                away_shots = fix_stat(away_shots)
                home_corners = fix_stat(home_corners)
                away_corners = fix_stat(away_corners)
                home_fouls = fix_stat(home_fouls)
                away_fouls = fix_stat(away_fouls)
                home_poss = fix_stat(home_poss)
                away_poss = fix_stat(away_poss)
                home_goals = fix_stat(home_goals)
                away_goals = fix_stat(away_goals)

                # Cálculo de totais
                total_shots = home_shots + away_shots
                total_corners = home_corners + away_corners
                total_fouls = home_fouls + away_fouls
                total_goals = home_goals + away_goals

                # Obtém nomes dos times (se disponíveis)
                home_team_name = match.get('home_name') or match.get('homeName') or match.get('team_a_name') or match.get('homeTeam')
                away_team_name = match.get('away_name') or match.get('awayName') or match.get('team_b_name') or match.get('awayTeam')
                if not home_team_name or not away_team_name:
                    continue

                # Estratégia 1: Over 0.5 HT com pressão
                if 25 <= elapsed_minutes <= 45:
                    # Verifica se algum time está pressionando (posse >= 60%, chutes >= 6, escanteios >= 4)
                    for team_side in ['home', 'away']:
                        poss = home_poss if team_side == 'home' else away_poss
                        shots = home_shots if team_side == 'home' else away_shots
                        corners = home_corners if team_side == 'home' else away_corners
                        if poss >= 60 and shots >= 6 and corners >= 4:
                            if (match_id, 1) not in sent_signals:
                                message = (f"⚽ Estratégia 1 (Over 0.5 HT): Possível gol no 1º tempo no jogo "
                                           f"{home_team_name} vs {away_team_name} - {elapsed_minutes}' "
                                           f"(Chutes: {shots}, Escanteios: {corners}, Posse: {poss}%)")
                                await send_message(message)
                                sent_signals.add((match_id, 1))
                            break  # Já encontrou pressão de um dos lados, não precisa verificar o outro

                # Estratégia 2: Over 1.5 FT com pressão
                if 50 <= elapsed_minutes <= 75 and total_goals == 0:
                    if total_shots >= 12 and total_corners >= 5:
                        if (match_id, 2) not in sent_signals:
                            message = (f"⚽ Estratégia 2 (Over 1.5 FT): Possível over 1.5 FT no jogo "
                                       f"{home_team_name} vs {away_team_name} - 0x0 aos {elapsed_minutes}' "
                                       f"(Chutes: {total_shots}, Escanteios: {total_corners})")
                            await send_message(message)
                            sent_signals.add((match_id, 2))

                # Estratégia 3: Cartões por faltas
                if elapsed_minutes <= 80:
                    if total_fouls >= 20 and total_corners >= 8 and total_shots >= 10:
                        if (match_id, 3) not in sent_signals:
                            message = (f"🟨 Estratégia 3 (Cartões): Possível cartão no jogo "
                                       f"{home_team_name} vs {away_team_name} - {elapsed_minutes}' "
                                       f"(Faltas: {total_fouls}, Escanteios: {total_corners}, Chutes: {total_shots})")
                            await send_message(message)
                            sent_signals.add((match_id, 3))

                # Estratégia 4: Escanteios prováveis
                if 10 <= elapsed_minutes <= 75:
                    if (home_poss >= 60 or away_poss >= 60) and total_shots >= 10 and total_corners <= 6:
                        if (match_id, 4) not in sent_signals:
                            dominant_poss = home_poss if home_poss >= away_poss else away_poss
                            message = (f"🚩 Estratégia 4 (Escanteios): Possível aposta em escanteios no jogo "
                                       f"{home_team_name} vs {away_team_name} - {elapsed_minutes}' "
                                       f"(Posse: {dominant_poss}%, Chutes: {total_shots}, Escanteios: {total_corners})")
                            await send_message(message)
                            sent_signals.add((match_id, 4))
            except Exception as e:
                print(f"Erro ao processar partida {match_id}: {e}")

        # Aguarda 120 segundos antes de verificar novamente
        await asyncio.sleep(120)

# Inicia o servidor Flask em uma thread separada
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()

# Executa o loop principal do bot
asyncio.run(main())
