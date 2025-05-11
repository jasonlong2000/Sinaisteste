import requests
from datetime import datetime
from telegram import Bot
import pytz
import time
import os

API_KEY = "6810ea1e7c44dab18f4fc039b73e8dd2"
BOT_TOKEN = "7430245294:AAGrVA6wHvM3JsYhPTXQzFmWJuJS2blam80"
CHAT_ID = "-1002675165012"

ARQUIVO_ENVIADOS = "pre_jogos_footballapi.txt"
ARQUIVO_RESULTADOS = "resultados_pendentes.txt"

bot = Bot(token=BOT_TOKEN)

LIGAS_PERMITIDAS = {
    2, 3, 4, 5, 9, 11, 13, 15, 32, 39, 40, 41, 48, 61, 62,
    66, 71, 72, 73, 75, 78, 79, 135, 140, 143, 145, 477, 484, 541, 556, 742, 866
}

HEADERS = {"x-apisports-key": API_KEY}

def carregar_enviados():
    if os.path.exists(ARQUIVO_ENVIADOS):
        with open(ARQUIVO_ENVIADOS, "r") as f:
            return set(line.strip() for line in f)
    return set()

def salvar_enviado(jogo_id):
    with open(ARQUIVO_ENVIADOS, "a") as f:
        f.write(f"{jogo_id}\n")

def salvar_resultado_previsto(jogo_id, time_home, time_away, previsao):
    with open(ARQUIVO_RESULTADOS, "a") as f:
        f.write(f"{jogo_id};{time_home};{time_away};{previsao}\n")

def buscar_jogos_do_dia():
    hoje = datetime.now().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={hoje}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", [])

def buscar_estatisticas(league_id, season, team_id):
    url = f"https://v3.football.api-sports.io/teams/statistics?league={league_id}&season={season}&team={team_id}"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("response", {})

def formatar_valor(v):
    return str(v) if v not in [None, "-", ""] else "0"

def sugestao_de_placar(gm1, gm2, gs1, gs2):
    try:
        g1 = round((float(gm1) + float(gs2)) / 2)
        g2 = round((float(gm2) + float(gs1)) / 2)
        alternativa = f"{g1+1} x {g2}" if g1 <= g2 else f"{g1} x {g2+1}"
        return f"{g1} x {g2} ou {alternativa}"
    except:
        return "Indefinido"
def gerar_sugestao(gm_home, gm_away, btts_home, btts_away,
                   clean_home, clean_away, first_goal_home, first_goal_away,
                   gs_home, gs_away, over15_home, over15_away, over25_home, over25_away,
                   minutos_home, minutos_away):
    try:
        gm_home = float(gm_home)
        gm_away = float(gm_away)
        gs_home = float(gs_home)
        gs_away = float(gs_away)
        over15_home = float(over15_home.strip('%'))
        over15_away = float(over15_away.strip('%'))
        over25_home = float(over25_home.strip('%'))
        over25_away = float(over25_away.strip('%'))
        btts_home = float(btts_home.strip('%'))
        btts_away = float(btts_away.strip('%'))
        fg_home = float(first_goal_home.strip('%'))
        clean_home = int(clean_home)
        clean_away = int(clean_away)

        alta_conf = []
        media_conf = []
        soma_gols = gm_home + gm_away + gs_home + gs_away
        btts_media = (btts_home + btts_away) / 2
        soma_ataque = gm_home + gm_away

        # Dupla Chance
        if gm_home >= 1.3 and gs_away >= 1.3:
            alta_conf.append("🔐 Dupla chance: 1X (alta)")
        elif gm_home >= 1.1 and gs_away >= 1.1:
            media_conf.append("🔐 Dupla chance: 1X (média)")

        if gm_away >= 1.3 and gs_home >= 1.3:
            alta_conf.append("🔐 Dupla chance: X2 (alta)")
        elif gm_away >= 1.1 and gs_home >= 1.1:
            media_conf.append("🔐 Dupla chance: X2 (média)")

        # Over 1.5 (com critérios de Over 2.5)
        if soma_ataque >= 2.8 and gs_home + gs_away >= 2.4 and over15_home >= 70 and over15_away >= 70:
            alta_conf.append("⚽ Over 1.5 gols (alta)")
        elif soma_ataque >= 2.6 and gs_home + gs_away >= 2.2 and over15_home >= 65 and over15_away >= 65:
            media_conf.append("⚠️ Over 1.5 gols (média)")

        # Outras estratégias (mantidas)
        under35_home = 3 - over25_home / 100 * 3
        under35_away = 3 - over25_away / 100 * 3
        if gm_home <= 1.0 and gm_away <= 1.0 and under35_home == 3 and under35_away == 3:
            alta_conf.append("🧤 Under 3.5 gols (alta)")
        elif gm_home <= 1.3 and gm_away <= 1.3 and under35_home >= 2.5 and under35_away >= 2.5:
            media_conf.append("🧤 Under 3.5 gols (média)")

        if btts_media >= 65 and gm_home >= 1.2 and gm_away >= 1.2:
            alta_conf.append("✅ Ambas Marcam (alta)")
        elif btts_media >= 60 and gm_home >= 1.0 and gm_away >= 1.0:
            media_conf.append("✅ Ambas Marcam (média)")

        faixas = ["0-15", "16-30", "31-45"]
        gols_ht_home = sum(1 for faixa in faixas if minutos_home.get(faixa, {}).get("total"))
        gols_ht_away = sum(1 for faixa in faixas if minutos_away.get(faixa, {}).get("total"))
        if gols_ht_home >= 2 and gols_ht_away >= 2 and fg_home >= 60:
            alta_conf.append("⏱️ Gol no 1º tempo (alta)")
        elif gols_ht_home >= 1 and gols_ht_away >= 1 and fg_home >= 50:
            media_conf.append("⏱️ Gol no 1º tempo (média)")

        if alta_conf or media_conf:
            return "\n".join(alta_conf + media_conf)
        else:
            return "Sem sugestão clara"
    except:
        return "Sem sugestão clara"

# Execução principal
if __name__ == "__main__":
    while True:
        verificar_pre_jogos()
        verificar_resultados()
        time.sleep(14400)  # A cada 4 horas
