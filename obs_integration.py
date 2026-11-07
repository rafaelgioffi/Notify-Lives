"""Integração opcional com fontes de texto do OBS via obs-websocket 5.x.

Isto atualiza textos exibidos no layout do OBS. O título/descrição da
plataforma (Twitch, YouTube etc.) continua dependente do serviço e não é
alterado por esta integração genérica.
"""


def atualizar_textos_obs(config):
    obs_config = config.get("obs", {})
    if not obs_config.get("habilitado", False):
        return

    try:
        import obsws_python as obs
    except ImportError:
        print("⚠️ OBS desativado: instale 'obsws-python' para atualizar as fontes de texto.")
        return

    cliente = None
    try:
        cliente = obs.ReqClient(
            host=obs_config.get("host", "localhost"),
            port=obs_config.get("porta", 4455),
            password=obs_config.get("senha", ""),
            timeout=3,
        )

        titulo = obs_config.get("fonte_titulo")
        descricao = obs_config.get("fonte_descricao")
        if titulo:
            cliente.set_input_settings(titulo, {"text": config["titulo_obs"]}, True)
        if descricao:
            cliente.set_input_settings(descricao, {"text": config["descricao_obs"]}, True)
        print("✅ Textos do OBS atualizados.")
    except Exception as erro:
        print(f"⚠️ Não foi possível atualizar o OBS: {erro}")
    finally:
        if cliente:
            cliente.disconnect()
