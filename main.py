def verificar_pre_jogos():
    jogos = buscar_jogos_do_dia()
    print(f"🔎 Total de jogos encontrados: {len(jogos)}")

    for jogo in jogos:
        try:
            fixture = jogo["fixture"]
            teams = jogo["teams"]
            league = jogo["league"]
            home = teams["home"]["name"]
            away = teams["away"]["name"]
            jogo_id = str(fixture["id"])
            status = fixture["status"]["short"]

            mensagem = f"🧪 Teste: *{home} x {away}*\nStatus: {status}\nLiga: {league['name']}\nID: {jogo_id}"
            print(f"📤 Enviando: {home} x {away}")
            bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
            time.sleep(1)

        except Exception as e:
            print(f"❌ Erro ao tentar enviar jogo: {e}")
            continue
