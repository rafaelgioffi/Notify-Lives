import pyautogui
pyautogui.FAILSAFE = False
import time
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pyperclip
import subprocess
import argparse
from playwright.sync_api import sync_playwright
from perfis import PERFIS, obter_perfil
from obs_integration import atualizar_textos_obs
from v2_app.channels.whatsapp_assisted import WhatsAppAssistedAdapter


def disparar_whatsapp_v2(config):
    """Envia para cada grupo, confirmando individualmente antes de prosseguir."""
    print("Iniciando disparo assistido no WhatsApp...")
    adapter = WhatsAppAssistedAdapter()
    grupos = config.get("grupos_whatsapp", [])

    for indice, grupo in enumerate(grupos, start=1):
        print(f"WhatsApp: grupo {indice}/{len(grupos)} - {grupo}")
        resultado = adapter.publish(
            destination=grupo,
            caption=config["mensagem"],
            media_path=config.get("caminho_imagem"),
            campaign_id=config.get("id", "manual"),
        )
        if resultado.success:
            print(f"WhatsApp confirmado para '{grupo}'.")
            continue

        print(f"Falha no WhatsApp para '{grupo}': {resultado.error_message}")
        resposta = input("Deseja seguir para o próximo grupo? [S/N]: ").strip().lower()
        if resposta not in {"s", "sim", "y", "yes"}:
            print("Envio do WhatsApp interrompido pelo usuário.")
            return
    
# --- PARTE 0: GERAR VÍDEO ANIMADO (REMOVIDO) ---
# A geração de vídeo foi removida pois você passará a usar vídeos gerados por IA.

# --- PARTE 1: WHATSAPP DESKTOP (RPA Simples) ---
def disparar_whatsapp(config):
    print("Iniciando disparo no WhatsApp...")
    mensagem = config["mensagem"]
    grupos_whatsapp = config["grupos_whatsapp"]
    caminho_imagem = config["caminho_imagem"]
    
    # Verifica se a imagem existe
    if not os.path.exists(caminho_imagem):
        print(f"⚠️ Imagem '{caminho_imagem}' não encontrada!")
    
    # O truque de mestre: forçar o Windows a chamar o WhatsApp para a frente
    os.system("start whatsapp://")
    time.sleep(5) # Aumentei o tempo de espera para o WhatsApp carregar bem
    
    for grupo in grupos_whatsapp:
        # Repõe a imagem na área de transferência para cada iteração, 
        # pois o pyperclip.copy da mensagem a sobrescreve!
        if os.path.exists(caminho_imagem):
            comando_ps = f"""
            Add-Type -AssemblyName System.Windows.Forms
            $img = [System.Drawing.Image]::FromFile('{caminho_imagem}')
            [System.Windows.Forms.Clipboard]::SetImage($img)
            """
            subprocess.run(['powershell', '-command', comando_ps])

        pyautogui.hotkey('ctrl', 'f') # Foca na busca
        time.sleep(1)
        pyautogui.write(grupo, interval=0.05) # Digita mais devagar
        time.sleep(2) # Tempo para buscar
        pyautogui.press(['tab', 'tab']) # Corrigido: 'tab 2' não funciona, precisa ser uma lista
        pyautogui.press('enter') # Entra no grupo
        time.sleep(1)
        
        # 1. Cola a imagem
        if os.path.exists(caminho_imagem):
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(2) # Aguarda a tela de anexo carregar
        
        # 2. Solução para mensagens incompletas e rápidas: Copiar e Colar (como legenda)
        pyperclip.copy(mensagem)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        
        pyautogui.press('enter') # Envia
        print(f"Mensagem enviada para {grupo}")
        time.sleep(1)

# --- PARTE 2: FACEBOOK (Playwright via CDP) ---
def disparar_facebook(config):
    print("Iniciando disparo no Facebook...")
    mensagem = config["mensagem"]
    grupos_facebook = config["grupos_facebook"]
    caminho_imagem = config["caminho_imagem"]
    habilitar_compartilhamento_grupos = config["habilitar_compartilhamento_grupos"]
    compartilhar_grupos_facebook = config["compartilhar_grupos_facebook"]
    
    # Cria uma pasta isolada para salvar o login do bot. Evita a falha de porta CDP.
    perfil_bot = os.path.join(os.getcwd(), "perfil_chrome_bot")
    
    with sync_playwright() as p:
        try:
            # Lança o navegador próprio em vez de tentar conectar a um Chrome existente
            context = p.chromium.launch_persistent_context(
                user_data_dir=perfil_bot,
                channel="chrome", # Usa o Google Chrome padrão
                headless=False,
                viewport={"width": 1920, "height": 1080},
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
                ignore_default_args=["--enable-automation"]
            )
            
            # Pega a aba padrão que foi aberta
            page = context.pages[0] if context.pages else context.new_page()

            for url_grupo in grupos_facebook:
                page.goto(url_grupo)
                page.wait_for_timeout(5000)
                
                # --- PAUSA PARA LOGIN SE NECESSÁRIO ---
                # Verifica se a página está pedindo login (ex: botão de Entrar visível)
                if page.locator("text='Entrar'").first.is_visible() or page.locator("input[type='password']").first.is_visible():
                    print("\n" + "="*60)
                    print("⚠️ O FACEBOOK ESTÁ PEDINDO LOGIN!")
                    print("👉 Vá para a janela do Chrome que o bot abriu e faça o login.")
                    print("⏳ O script está pausado aguardando você terminar...")
                    input("👉 APERTE 'ENTER' AQUI NESTE TERMINAL APÓS LOGAR PARA CONTINUAR...")
                    print("="*60 + "\n")
                    
                    # Recarrega a página após o login para garantir que está na página certa
                    page.goto(url_grupo)
                    page.wait_for_timeout(5000)

                try:
                    # Seletores podem variar. Tenta várias opções comuns
                    caixa_texto = None
                    for seletor in [
                        "text='Escreva algo...'", 
                        "text='No que você está pensando'", 
                        "text='No que você está pensando?'",
                        "text='Criar publicação'",
                        "[aria-label='Criar uma publicação']"
                    ]:
                        elemento = page.locator(seletor).first
                        if elemento.is_visible():
                            caixa_texto = elemento
                            break
                        
                    if caixa_texto:
                        caixa_texto.click(timeout=5000)
                        page.wait_for_timeout(2000)
                        
                        # Insere a mensagem
                        page.keyboard.insert_text(mensagem) 
                        page.wait_for_timeout(2000)
                        
                        # Adiciona a imagem
                        if os.path.exists(caminho_imagem):
                            try:
                                with page.expect_file_chooser(timeout=5000) as fc_info:
                                    # Tenta clicar no botão de Foto/vídeo
                                    botao_foto = page.locator("div[aria-label='Foto/vídeo']").first
                                    if not botao_foto.is_visible():
                                        botao_foto = page.locator("text='Foto/vídeo'").first
                                    if not botao_foto.is_visible():
                                        # Alternativa novo layout do Facebook
                                        botao_foto = page.locator("div[aria-label='Adicionar à sua publicação']").first
                                    botao_foto.click(force=True)
                                
                                file_chooser = fc_info.value
                                file_chooser.set_files(caminho_imagem)
                                print("Imagem anexada no Facebook.")
                                page.wait_for_timeout(4000) # Aguarda upload da imagem
                            except Exception as e:
                                print(f"⚠️ Não foi possível anexar a imagem no Facebook com clique: {e}")
                                print("Tentando setar o arquivo via input oculto...")
                                try:
                                    input_file = page.locator("input[type='file'][accept*='image']").first
                                    input_file.set_files(caminho_imagem)
                                    print("Imagem anexada no Facebook (via input).")
                                    page.wait_for_timeout(4000)
                                except Exception as e2:
                                    print(f"⚠️ Falha total ao anexar imagem no Facebook: {e2}")
                        
                        # Clica em Avançar (comentário corrigido de Publicar)
                        try:
                            botao_avancar = page.locator("div[aria-label='Avançar']").first
                            if not botao_avancar.is_visible():
                                botao_avancar = page.locator("text='Avançar'").last
                            
                            botao_avancar.click(timeout=8000)
                            page.wait_for_timeout(2000) # Aguarda popup carregar
                        except Exception as e_avancar:
                            print("\n" + "="*60)
                            print("⚠️ O FACEBOOK DEMOROU OU DEU TIMEOUT NO BOTÃO DE AVANÇAR!")
                            print("Se você selecionou o vídeo/imagem manualmente, finalize a postagem você mesmo agora.")
                            input("👉 APERTE 'ENTER' AQUI NESTE TERMINAL APÓS CONCLUIR PARA IR PARA A PRÓXIMA REDE...")
                            print("="*60 + "\n")
                            continue # Pula o resto das etapas deste grupo/página, pois o usuário fará manual
                        
                        falhou_ao_marcar_grupos = False
                        
                        # --- COMPARTILHAR NOS GRUPOS ---
                        if habilitar_compartilhamento_grupos and len(compartilhar_grupos_facebook) > 0:
                            page.locator("text='Compartilhar nos grupos'").first.click()
                            page.wait_for_timeout(3500) # Aguarda lista de grupos carregar bem
                            
                            for grupo_fb in compartilhar_grupos_facebook:
                                try:
                                    # Usa .last pois popups/modais no Facebook ficam no fim do código da página
                                    # force=True garante o clique ignorando se o Facebook botou algum 'overlay' por cima
                                    elemento_grupo = page.get_by_text(grupo_fb, exact=False).last
                                    elemento_grupo.click(timeout=4000, force=True)
                                    page.wait_for_timeout(1000)
                                    print(f"✅ Grupo selecionado: {grupo_fb}")
                                except Exception as e:
                                    print(f"⚠️ Não foi possível achar/marcar o grupo '{grupo_fb}'.")
                                    falhou_ao_marcar_grupos = True
                                    # Salva um print específico desse erro para entendermos o que rolou
                                    caminho_erro_grupo = os.path.join(os.getcwd(), f"erro_grupo_{grupo_fb[:5]}.png")
                                    page.screenshot(path=caminho_erro_grupo)
                                    print(f"📸 Print salvo em: {caminho_erro_grupo} com o detalhe do erro.")
                            
                            if falhou_ao_marcar_grupos:
                                print("❌ Postagem abortada: A opção de grupos está ativada mas não foi possível marcar um ou mais grupos.")
                                continue # Interrompe a postagem nessa URL e vai para a próxima (se houver)
                                
                            # Clica em Concluir
                            botao_concluir = page.locator("div[aria-label='Concluir']").first
                            if not botao_concluir.is_visible():
                                botao_concluir = page.locator("text='Concluir'").last
                            botao_concluir.click()
                            page.wait_for_timeout(1500)
                            
                        # Clica no botão final de Postar
                        botao_postar = page.locator("div[aria-label='Postar']").first
                        if not botao_postar.is_visible():
                            botao_postar = page.locator("text='Postar'").last
                            
                        botao_postar.click()
                        print(f"Postado no grupo/página: {url_grupo} com sucesso!")
                    else:
                        print(f"⚠️ Erro: Não encontrei a caixa de texto para postar em {url_grupo}.")
                        print("Verifique se você tem permissão para postar aí ou se o layout mudou.")
                        
                except Exception as e:
                    print(f"Erro ao postar no grupo {url_grupo}: {e}")
                
                # Aumentei o tempo de espera no final para 15 segundos! 
                # Isso garante que o clique no Postar seja finalizado antes do Chrome fechar.
                print("Aguardando 15 segundos para o Facebook processar o envio...")
                page.wait_for_timeout(15000)
                
            context.close() 
            
        except Exception as e:
            print("ERRO DE CONEXÃO: Certifique-se de ter fechado janelas antigas do perfil do bot.")
            print(f"Detalhe: {e}")

        finally:
            context.close()

# --- PARTE 3: INSTAGRAM (Playwright) ---
def disparar_instagram(config):
    print("Iniciando disparo no Instagram...")
    mensagem = config["mensagem"]
    caminho_imagem = config["caminho_imagem"]
    
    perfil_bot = os.path.join(os.getcwd(), "perfil_chrome_bot")
    
    if not os.path.exists(caminho_imagem):
        print(f"⚠️ ERRO: Imagem '{caminho_imagem}' não encontrada! Pulo Instagram.")
        return

    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=perfil_bot,
                channel="chrome",
                headless=False,
                viewport={"width": 1920, "height": 1080},
                locale="pt-BR",
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
                ignore_default_args=["--enable-automation"]
            )
            
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://www.instagram.com/")
            page.wait_for_timeout(5000)
            
            # --- PAUSA PARA LOGIN SE NECESSÁRIO ---
            while page.locator("input[name='username']").first.is_visible() or page.locator("text='Entrar'").first.is_visible() or "challenge" in page.url:
                print("\n" + "="*60)
                print("⚠️ O INSTAGRAM ESTÁ PEDINDO LOGIN OU RESOLVER UM CAPTCHA!")
                print("👉 Vá para a janela do Chrome que o bot abriu, faça o login e resolva o 'Não sou robô'.")
                print("👉 SÓ VOLTE AQUI E APERTE ENTER QUANDO ESTIVER VENDO A PÁGINA INICIAL DO SEU INSTAGRAM!")
                print("⏳ O script está pausado aguardando você terminar...")
                input("👉 APERTE 'ENTER' AQUI NESTE TERMINAL APÓS LOGAR PARA CONTINUAR...")
                print("="*60 + "\n")
                page.goto("https://www.instagram.com/")
                page.wait_for_timeout(5000)

            # Lidar com popups "Ativar notificações" ou "Salvar informações" (se aparecerem)
            try:
                if page.locator("text='Agora não'").first.is_visible():
                    page.locator("text='Agora não'").first.click(timeout=3000)
                    page.wait_for_timeout(2000)
                if page.locator("text='Agora não'").first.is_visible():
                    page.locator("text='Agora não'").first.click(timeout=3000)
                    page.wait_for_timeout(2000)
            except Exception:
                pass

            try:
                # Clica em Criar
                try:
                    botao_criar = page.get_by_role("link", name="Nova publicação").first
                    if not botao_criar.is_visible():
                        botao_criar = page.locator("svg[aria-label='Nova publicação']").first
                    if not botao_criar.is_visible():
                        botao_criar = page.locator("text='Criar'").first
                        
                    if botao_criar.is_visible():
                        botao_criar.click(force=True, timeout=5000)
                    else:
                        raise Exception("Botão de Criar não está visível.")
                except Exception as e_criar:
                    print("\n" + "="*60)
                    print("⚠️ O INSTAGRAM NÃO MOSTROU O BOTÃO DE CRIAR!")
                    print("Isso geralmente acontece se houver um CAPTCHA de segurança (reCAPTCHA) bloqueando a tela.")
                    print("👉 Vá para a janela do Chrome que o bot abriu e resolva o desafio de imagens.")
                    print("⏳ O script está pausado aguardando...")
                    input("👉 APERTE 'ENTER' AQUI NESTE TERMINAL APÓS RESOLVER O CAPTCHA PARA CONTINUAR...")
                    print("="*60 + "\n")
                    # Após apertar enter, recarrega a página
                    page.goto("https://www.instagram.com/")
                    page.wait_for_timeout(5000)
                    # Tenta pegar o botão de novo e clicar forçadamente
                    botao_criar = page.locator("svg[aria-label='Nova publicação']").first
                    botao_criar.click(force=True, timeout=5000)
                
                page.wait_for_timeout(2000)
                
                # Se abrir um submenu "Publicação", clica nela
                botao_publicacao = page.locator("text='Publicação'").first
                if botao_publicacao.is_visible():
                    botao_publicacao.click()
                    page.wait_for_timeout(2000)

                # Fazer upload do arquivo
                with page.expect_file_chooser() as fc_info:
                    page.locator("text='Selecionar do computador'").first.click()
                file_chooser = fc_info.value
                file_chooser.set_files(caminho_imagem)
                
                page.wait_for_timeout(3000)
                
                # Avançar (Filtros)
                page.locator("text='Avançar'").first.click()
                page.wait_for_timeout(2000)
                
                # Avançar (Ajustes)
                page.locator("text='Avançar'").first.click()
                page.wait_for_timeout(2000)
                
                # Escrever legenda
                caixa_legenda = page.locator("div[aria-label='Escreva uma legenda...']").first
                if not caixa_legenda.is_visible():
                    caixa_legenda = page.locator("textarea").first
                caixa_legenda.click()
                page.keyboard.insert_text(mensagem)
                page.wait_for_timeout(2000)
                
                # Compartilhar
                page.locator("text='Compartilhar'").first.click()
                print("Publicando no Instagram...")
                
                # Aguarda confirmação
                page.wait_for_selector("text='Sua publicação foi compartilhada.'", timeout=20000)
                print("✅ Postado no Instagram com sucesso!")
                
                page.wait_for_timeout(2000)
                
            except Exception as e:
                print(f"Erro ao postar no Instagram: {e}")
                caminho_erro = os.path.join(os.getcwd(), "erro_instagram.png")
                page.screenshot(path=caminho_erro)
                print(f"📸 Print salvo em: {caminho_erro} com o detalhe do erro.")

        except Exception as e:
            print(f"ERRO DE CONEXÃO NO INSTAGRAM: {e}")
        finally:
            context.close()

# --- PARTE 4: TIKTOK (Playwright) ---
def disparar_tiktok(config):
    print("Iniciando disparo no TikTok...")
    mensagem = config["mensagem"]
    caminho_video = config["caminho_video"]
    
    perfil_bot = os.path.join(os.getcwd(), "perfil_chrome_bot")
    
    if not os.path.exists(caminho_video):
        print(f"⚠️ ERRO: Vídeo '{caminho_video}' não encontrado! Pulo TikTok.")
        return

    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=perfil_bot,
                channel="chrome",
                headless=False,
                viewport={"width": 1920, "height": 1080},
                locale="pt-BR",
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
                ignore_default_args=["--enable-automation"]
            )
            
            page = context.pages[0] if context.pages else context.new_page()
            
            # Vai direto para a página de upload do Creator Center
            page.goto("https://www.tiktok.com/creator-center/upload?scene=creator_center")
            page.wait_for_timeout(8000) # TikTok é pesado
            
            if page.locator("text='Entrar'").first.is_visible() or page.url.startswith("https://www.tiktok.com/login"):
                print("\n" + "="*60)
                print("⚠️ O TIKTOK ESTÁ PEDINDO LOGIN!")
                print("👉 Vá para a janela do Chrome que o bot abriu e faça o login manualmente.")
                print("⏳ O script está pausado aguardando você terminar...")
                input("👉 APERTE 'ENTER' AQUI NESTE TERMINAL APÓS LOGAR PARA CONTINUAR...")
                print("="*60 + "\n")
                page.goto("https://www.tiktok.com/creator-center/upload?scene=creator_center")
                page.wait_for_timeout(8000)

            try:
                print("Procurando área de upload de arquivo no TikTok...")
                
                # Tenta clicar no botão de 'Selecionar vídeo' que abre a janela do sistema
                try:
                    with page.expect_file_chooser(timeout=10000) as fc_info:
                        botao_selecionar = page.locator("text='Selecionar vídeo'").first
                        if not botao_selecionar.is_visible():
                            botao_selecionar = page.locator("text='Select video'").first
                        
                        # Clica forçado caso tenha alguma div por cima
                        botao_selecionar.click(force=True)
                    
                    file_chooser = fc_info.value
                    file_chooser.set_files(caminho_video)
                except Exception as ex_btn:
                    print("Não foi possível clicar no botão Selecionar vídeo, tentando fallback (input oculto)...")
                    page.wait_for_selector("input[type='file']", timeout=10000, state="attached")
                    input_file = page.locator("input[type='file']").first
                    input_file.set_files(caminho_video)
                
                print("Arquivo selecionado! Aguardando processamento do upload...")
                page.wait_for_timeout(10000)
                
                # Preenche a legenda
                legenda_box = page.locator(".DraftEditor-root").first
                if not legenda_box.is_visible():
                    legenda_box = page.locator("[role='combobox']").first
                    
                if legenda_box.is_visible():
                    legenda_box.click()
                    page.keyboard.insert_text(mensagem)
                    page.wait_for_timeout(2000)
                else:
                    print("⚠️ Não achei a caixa de legenda no TikTok.")
                
                # Clica em Publicar
                botao_postar = page.locator("text='Publicar'").first
                if botao_postar.is_visible():
                    botao_postar.click()
                    print("Botão publicar clicado!")
                    page.wait_for_timeout(10000)
                    print("✅ Postado no TikTok com sucesso!")
                else:
                    print("⚠️ Não achei o botão Publicar no TikTok!")
                    
            except Exception as e:
                print(f"Erro ao postar no TikTok: {e}")
                caminho_erro = os.path.join(os.getcwd(), "erro_tiktok.png")
                page.screenshot(path=caminho_erro)
                print(f"📸 Print salvo em: {caminho_erro} com o detalhe do erro.")

        except Exception as e:
            print(f"ERRO DE CONEXÃO NO TIKTOK: {e}")
        finally:
            context.close()


def selecionar_perfil():
    """Permite escolher o jogo sem usar parâmetros na linha de comando."""
    opcoes = list(sorted(PERFIS.items()))
    print("\nEscolha o perfil da live:\n")
    for indice, (_, config) in enumerate(opcoes, start=1):
        print(f"  {indice}. {config['nome']}")

    while True:
        escolha = input("\nDigite o número do perfil (ou 0 para sair): ").strip()
        if escolha == "0":
            raise SystemExit("Operação cancelada.")
        if escolha.isdigit() and 1 <= int(escolha) <= len(opcoes):
            return opcoes[int(escolha) - 1][1]
        print("Opção inválida. Escolha um dos números exibidos.")

# --- EXECUÇÃO ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publica a divulgação da live em várias redes sociais.")
    parser.add_argument(
        "--perfil",
        choices=sorted(PERFIS),
        help="Perfil do jogo a divulgar. Se omitido, abre o menu interativo.",
    )
    args = parser.parse_args()
    perfil = obter_perfil(args.perfil) if args.perfil else selecionar_perfil()

    print(f"Perfil selecionado: {perfil['nome']}")
    atualizar_textos_obs(perfil)
    disparar_whatsapp_v2(perfil)
    disparar_facebook(perfil)
    disparar_instagram(perfil)
    disparar_tiktok(perfil)
    print("Automação concluída! Boa live!")
