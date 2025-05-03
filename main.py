import os
import requests
import time
import threading
import asyncio
from flask import Flask

# Configurações do bot e API
# Obtenha o token do bot do Telegram, o chat_id do canal/usuário e a chave da API FootyStats de variáveis de ambiente
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FOOTY_API_KEY = os.environ.get("FOOTY_API_KEY")

# Se preferir, pode substituir os env acima por valores diretamente (não recomendado deixar exposto)
# TELEGRAM_TOKEN = "seu_token_aqui"
# TELEGRAM_CHAT_ID = "seu_chat_id_aqui"
# FOOTY_API_KEY = "sua_chave_api_aqui"

# Verificação simples se as configurações estão presentes
if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID or not FOOTY_API_KEY:
    print("ERRO: Configure TELEGRAM_TOKEN, TELEGRAM_CHAT_ID e FOOTY_API_KEY nas variáveis de ambiente.")
    # Não encerramos aqui para permitir teste local sem variáveis de ambiente definidas

# URL base das APIs
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
FOOTY_API_URL = "https://api.football-data-api.com"

# Cria aplicativo Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot de Sinais Esportivos está rodando."

# Dicionário para cache de nomes de times já obtidos (evita chamar API repetidamente para o mesmo time)
team_names_cache = {}

def get_team_name(team_id):
    """Obtém o nome do time a partir do ID usando a API FootyStats (com cache)."""
    if team_id in team_names_cache:
        return team_names_cache[team_id]
    try:
        # Chama o endpoint da API para informações do time
        url = f"{FOOTY_API_URL}/team?key={FOOTY_API_KEY}&team_id={team_id}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        team_data = None
        if isinstance(data, dict) and "data" in data:
            # A resposta pode vir como lista (vários registros por temporadas) ou dict único
            if isinstance(data["data"], list):
                if data["data"]:
                    team_data = data["data"][0]  # pega o primeiro registro
            elif isinstance(data["data"], dict):
                team_data = data["data"]
        name = None
        if team_data:
            # Tenta usar o nome padrão do time
            name = team_data.get("name")
            if not name or name.strip() == "":
                name = team_data.get("full_name") or team_data.get("english_name")
            # Se existir nome em português fornecido, utiliza-o
            name_pt = team_data.get("name_pt")
            if name_pt and isinstance(name_pt, str) and name_pt.strip() != "":
                name = name_pt
        if not name:
            name = str(team_id)  # fallback: usa o ID como nome se não encontrado
        team_names_cache[team_id] = name
        return name
    except Exception as e:
        print(f"Erro ao obter nome do time {team_id}: {e}")
        return str(team_id)

# Conjuntos para rastrear sinais já enviados e evitar duplicados
signaled_matches = {"S1": set(), "S2": set(), "S3": set(), "S4": set()}
alerted_matches = {"S1": set(), "S2": set(), "S3": set(), "S4": set()}

def send_telegram_message(text):
    """Envia uma mensagem de texto via Telegram bot para o chat configurado."""
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
        # Envia solicitação HTTP POST para a API do Telegram
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Erro ao enviar mensagem Telegram: {e}")

def check_and_send_signals():
    """Consulta a API FootyStats por jogos ao vivo e aplica as estratégias, enviando sinais/alertas."""
    try:
        # Consulta partidas de hoje (inclui partidas em andamento) com estatísticas atualizadas
        url = f"{FOOTY_API_URL}/todays-matches?key={FOOTY_API_KEY}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
    except Exception as e:
        print(f"Erro ao consultar partidas: {e}")
        return  # em caso de erro na API, aborta este ciclo

    if not data.get("success"):
        # Verifica se a resposta indica sucesso
        print(f"Falha na resposta da API de partidas: {data}")
        return

    matches = data.get("data", [])
    for match in matches:
        try:
            status = match.get("status")
            # Ignora partidas já finalizadas ou não iniciadas (status 'complete' ou sem dados de stats)
            if status != "incomplete":
                continue

            match_id = match.get("id")
            home_goals = match.get("homeGoalCount", 0)
            away_goals = match.get("awayGoalCount", 0)

            # Verifica se a partida possui dados de estatísticas (se não, possivelmente ainda não começou)
            if match.get("team_a_shots") == -1 and match.get("team_a_shotsOnTarget") == -1:
                # Sem dados disponíveis de stats, pula para o próximo jogo
                continue

            # Calcula minuto atual aproximado usando timestamp de início, se disponível
            current_minute = None
            if match.get("date_unix"):
                try:
                    kickoff_ts = int(match["date_unix"])
                    elapsed = time.time() - kickoff_ts  # segundos desde o início
                    if elapsed < 0:
                        current_minute = 0
                    else:
                        minute = int(elapsed // 60)
                        # Limita minuto máximo a 90 (não consideramos possíveis acréscimos/extra)
                        if minute > 90:
                            minute = 90
                        current_minute = minute
                except Exception:
                    current_minute = None

            # Extrai estatísticas da partida
            shots_home = match.get("team_a_shots", 0)
            shots_away = match.get("team_b_shots", 0)
            shots_on_target_home = match.get("team_a_shotsOnTarget", 0)
            shots_on_target_away = match.get("team_b_shotsOnTarget", 0)
            corners_home = match.get("team_a_corners", 0)
            corners_away = match.get("team_b_corners", 0)
            fouls_home = match.get("team_a_fouls", 0)
            fouls_away = match.get("team_b_fouls", 0)
            poss_home = match.get("team_a_possession", 0)
            poss_away = match.get("team_b_possession", 0)

            # Substitui valores padrão negativos por 0 (significa ausência de dado, tratamos como 0)
            if shots_home < 0: shots_home = 0
            if shots_away < 0: shots_away = 0
            if shots_on_target_home < 0: shots_on_target_home = 0
            if shots_on_target_away < 0: shots_on_target_away = 0
            if corners_home < 0: corners_home = 0
            if corners_away < 0: corners_away = 0
            if fouls_home < 0: fouls_home = 0
            if fouls_away < 0: fouls_away = 0
            if poss_home < 0 or poss_away < 0:
                poss_home = poss_away = 0  # se posse não disponível, zera ambos

            # Calcula estatísticas combinadas e derivadas
            total_shots = shots_home + shots_away
            total_shots_on_target = shots_on_target_home + shots_on_target_away
            total_corners = corners_home + corners_away
            total_fouls = fouls_home + fouls_away
            # Maior posse de bola (para identificar se algum time >= 60% de posse)
            max_possession = poss_home if poss_home >= poss_away else poss_away

            # Obtém nomes das equipes
            home_team_name = get_team_name(match.get("homeID"))
            away_team_name = get_team_name(match.get("awayID"))

            # Texto do placar e minuto para usar nas mensagens
            score_text = f"{home_goals}x{away_goals}"
            minute_text = f"{current_minute}'" if current_minute is not None else ""

            # Estratégia 1: Over 0.5 HT (gol no 1º tempo)
            if current_minute is None or (25 <= current_minute <= 45):
                strat = "S1"
                if total_shots_on_target >= 6 and total_corners >= 4 and max_possession >= 60:
                    # Critérios atendidos -> envia sinal se não enviado antes
                    if match_id not in signaled_matches[strat]:
                        message = (f"🚨 Sinal Over 0.5 HT:\n"
                                   f"{home_team_name} vs {away_team_name} - {score_text} {minute_text}\n"
                                   f"Chutes no alvo: {total_shots_on_target}, Escanteios: {total_corners}, "
                                   f"Posse de bola: {poss_home}% - {poss_away}%")
                        send_telegram_message(message)
                        signaled_matches[strat].add(match_id)
                else:
                    # Critérios quase atingidos -> envia alerta "analisando" se ainda não enviado
                    if total_shots_on_target >= 4 and total_corners >= 3 and max_possession >= 55:
                        if match_id not in alerted_matches[strat] and match_id not in signaled_matches[strat]:
                            message = (f"👀 Analisando (Over 0.5 HT):\n"
                                       f"{home_team_name} vs {away_team_name} - {score_text} {minute_text}\n"
                                       f"Chutes no alvo: {total_shots_on_target}, Escanteios: {total_corners}, "
                                       f"Posse: {poss_home}% - {poss_away}%")
                            send_telegram_message(message)
                            alerted_matches[strat].add(match_id)

            # Estratégia 2: Over 1.5 FT (2 ou mais gols no jogo)
            if current_minute is None or (50 <= current_minute <= 75):
                strat = "S2"
                if home_goals == 0 and away_goals == 0:  # só consideramos se está 0x0
                    if total_shots >= 12 and total_corners >= 5:
                        if match_id not in signaled_matches[strat]:
                            message = (f"🚨 Sinal Over 1.5 FT:\n"
                                       f"{home_team_name} vs {away_team_name} - {score_text} {minute_text}\n"
                                       f"Chutes: {total_shots}, Escanteios: {total_corners}")
                            send_telegram_message(message)
                            signaled_matches[strat].add(match_id)
                    else:
                        if total_shots >= 8 and total_corners >= 4:
                            if match_id not in alerted_matches[strat] and match_id not in signaled_matches[strat]:
                                message = (f"👀 Analisando (Over 1.5 FT):\n"
                                           f"{home_team_name} vs {away_team_name} - {score_text} {minute_text}\n"
                                           f"Chutes: {total_shots}, Escanteios: {total_corners}")
                                send_telegram_message(message)
                                alerted_matches[strat].add(match_id)

            # Estratégia 3: Cartões (jogo truncado, muitas faltas)
            if current_minute is None or current_minute <= 80:
                strat = "S3"
                if total_fouls >= 20 and total_shots >= 10 and total_corners >= 8:
                    if match_id not in signaled_matches[strat]:
                        message = (f"🚨 Sinal Cartões:\n"
                                   f"{home_team_name} vs {away_team_name} - {score_text} {minute_text}\n"
                                   f"Faltas: {total_fouls}, Chutes: {total_shots}, Escanteios: {total_corners}")
                        send_telegram_message(message)
                        signaled_matches[strat].add(match_id)
                else:
                    if total_fouls >= 15 and total_shots >= 7 and total_corners >= 6:
                        if match_id not in alerted_matches[strat] and match_id not in signaled_matches[strat]:
                            message = (f"👀 Analisando (Cartões):\n"
                                       f"{home_team_name} vs {away_team_name} - {score_text} {minute_text}\n"
                                       f"Faltas: {total_fouls}, Chutes: {total_shots}, Escanteios: {total_corners}")
                            send_telegram_message(message)
                            alerted_matches[strat].add(match_id)

            # Estratégia 4: Escanteios (jogo com domínio e poucos escanteios, chance de muitos cantos na sequência)
            if current_minute is None or (10 <= current_minute <= 75):
                strat = "S4"
                if total_corners <= 6:  # somente se ainda há 6 ou menos escanteios no jogo
                    if total_shots >= 10 and max_possession >= 60:
                        if match_id not in signaled_matches[strat]:
                            message = (f"🚨 Sinal Escanteios:\n"
                                       f"{home_team_name} vs {away_team_name} - {score_text} {minute_text}\n"
                                       f"Chutes: {total_shots}, Escanteios: {total_corners}, "
                                       f"Posse de bola: {poss_home}% - {poss_away}%")
                            send_telegram_message(message)
                            signaled_matches[strat].add(match_id)
                    else:
                        if total_shots >= 7 and max_possession >= 55:
                            if match_id not in alerted_matches[strat] and match_id not in signaled_matches[strat]:
                                message = (f"👀 Analisando (Escanteios):\n"
                                           f"{home_team_name} vs {away_team_name} - {score_text} {minute_text}\n"
                                           f"Chutes: {total_shots}, Escanteios: {total_corners}, "
                                           f"Posse: {poss_home}% - {poss_away}%")
                                send_telegram_message(message)
                                alerted_matches[strat].add(match_id)
        except Exception as e:
            print(f"Erro ao processar partida {match.get('id')}: {e}")

async def background_loop():
    """Loop assíncrono que verifica partidas ao vivo a cada 2 minutos."""
    while True:
        # Executa a checagem de sinais em uma thread separada (para não bloquear caso usemos await)
        await asyncio.to_thread(check_and_send_signals)
        # Aguarda 2 minutos (120 segundos) para a próxima checagem
        await asyncio.sleep(120)

def start_background_loop():
    """Inicia o loop assíncrono de verificação em uma thread separada."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(background_loop())

# Inicia a thread de background antes de rodar o servidor Flask
threading.Thread(target=start_background_loop, daemon=True).start()

# Executa o servidor Flask no host 0.0.0.0 e porta definida (usado em ambientes de hospedagem como Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
