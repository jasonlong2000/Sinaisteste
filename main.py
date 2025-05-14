def gerar_sugestao(stats_home, stats_away):
    try:
        gm_home = float(stats_home["goals"]["for"]["average"]["total"])
        gm_away = float(stats_away["goals"]["for"]["average"]["total"])
        gs_home = float(stats_home["goals"]["against"]["average"]["total"])
        gs_away = float(stats_away["goals"]["against"]["average"]["total"])
        btts_home = float(stats_home["both_teams_to_score"]["percentage"].strip('%'))
        btts_away = float(stats_away["both_teams_to_score"]["percentage"].strip('%'))
        clean_home = int(stats_home["clean_sheet"]["total"])
        clean_away = int(stats_away["clean_sheet"]["total"])
        fg_home = float(stats_home["first_goal"]["for"]["percentage"].strip('%'))
        fg_away = float(stats_away["first_goal"]["for"]["percentage"].strip('%'))
        shots_on_home = float(stats_home["shots"]["on"]["average"]["total"])
        shots_on_away = float(stats_away["shots"]["on"]["average"]["total"])

        alta_conf = []
        media_conf = []

        # Dupla Chance - 1X
        if gm_home >= 1.3 and gs_away >= 1.3 and fg_home >= 60:
            alta_conf.append("🔐 Dupla chance: 1X (alta)")
        elif gm_home >= 1.1 and gs_away >= 1.1 and fg_home >= 50:
            media_conf.append("🔐 Dupla chance: 1X (média)")

        # Dupla Chance - X2
        if gm_away >= 1.3 and gs_home >= 1.3 and fg_away >= 60:
            alta_conf.append("🔐 Dupla chance: X2 (alta)")
        elif gm_away >= 1.1 and gs_home >= 1.1 and fg_away >= 50:
            media_conf.append("🔐 Dupla chance: X2 (média)")

        # Over 1.5
        soma_gols = gm_home + gm_away
        soma_sofridos = gs_home + gs_away

        if soma_gols >= 2.5 and soma_sofridos >= 1.5:
            alta_conf.append("⚽ Over 1.5 gols (alta)")
        elif soma_gols >= 2.0 and soma_sofridos >= 1.0:
            media_conf.append("⚠️ Over 1.5 gols (média)")

        # Under 3.5
        clean_total = clean_home + clean_away
        shots_total = shots_on_home + shots_on_away
        btts_total = btts_home + btts_away

        if clean_total >= 6 and shots_total < 7 and btts_total < 120:
            alta_conf.append("🧤 Under 3.5 gols (alta)")
        elif clean_total >= 4 and shots_total < 9 and btts_total < 140:
            media_conf.append("🧤 Under 3.5 gols (média)")

        return "\n".join(alta_conf + media_conf) if alta_conf or media_conf else "Sem sugestão clara"
    except:
        return "Sem sugestão clara"

def verificar_pre_jogos():
    enviados = carregar_enviados()
    jogos = buscar_jogos_do_dia()
    for jogo in jogos:
        fixture = jogo["fixture"]
        jogo_id = str(fixture["id"])
        if fixture["status"]["short"] != "NS" or jogo_id in enviados:
            continue
        mensagem = formatar_jogo(jogo)
        if mensagem:
            bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
            salvar_enviado(jogo_id)
            time.sleep(2)

def verificar_resultados():
    if not os.path.exists(ARQUIVO_RESULTADOS):
        return
    with open(ARQUIVO_RESULTADOS, "r") as f:
        linhas = f.readlines()

    alto_total = alto_green = 0
    medio_total = medio_green = 0

    for linha in linhas:
        jogo_id, time_home, time_away, previsao = linha.strip().split(";")
        url = f"https://v3.football.api-sports.io/fixtures?id={jogo_id}"
        res = requests.get(url, headers=HEADERS).json()
        if not res["response"]:
            continue
        jogo = res["response"][0]
        if jogo["fixture"]["status"]["short"] != "FT":
            continue

        gols_home = jogo["goals"]["home"]
        gols_away = jogo["goals"]["away"]
        entradas = previsao.split(" | ")
        resultado = []

        for entrada in entradas:
            tipo = "alto" if "(alta" in entrada else "medio"
            acertou = False
            if "Over 1.5" in entrada and (gols_home + gols_away) >= 2:
                acertou = True
            if "Under 3.5" in entrada and (gols_home + gols_away) <= 3:
                acertou = True
            if "Dupla chance: 1X" in entrada and gols_home >= gols_away:
                acertou = True
            if "Dupla chance: X2" in entrada and gols_away >= gols_home:
                acertou = True

            if tipo == "alto":
                alto_total += 1
                if acertou: alto_green += 1
            elif tipo == "medio":
                medio_total += 1
                if acertou: medio_green += 1

            resultado.append(f"{'✅' if acertou else '❌'} {entrada}")

        resumo = (
            f"📊 *{time_home} x {time_away}* terminou {gols_home} x {gols_away}\n"
            f"🎯 Previsões:\n" + "\n".join(resultado)
        )
        bot.send_message(chat_id=CHAT_ID, text=resumo, parse_mode="Markdown")

    final = f"📈 *Resumo final:*\n"
    final += f"⭐ Risco alto: {alto_green}/{alto_total} green\n" if alto_total else ""
    final += f"⚠️ Risco médio: {medio_green}/{medio_total} green" if medio_total else ""
    bot.send_message(chat_id=CHAT_ID, text=final, parse_mode="Markdown")

if __name__ == "__main__":
    bot.send_message(chat_id=CHAT_ID, text="✅ Robô de previsões ativado com sucesso!")
    while True:
        verificar_pre_jogos()
        verificar_resultados()
        time.sleep(14400)
