import pyautogui
pyautogui.FAILSAFE = False
import time
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pyperclip
import subprocess
from playwright.sync_api import sync_playwright

# --- CONFIGURAÇÕES ---
mensagem = """Fala galera! Tudo bem com vcs? Estamos ao vivo jogando Heroes Olden Era!
O melhor conteúdo sobre HOMM:OE do Brasil!
O bicho tá pegando na campanha... 😅

Cola lá:
🟣 https://twitch.tv/CabruncoGamesBR
🟢 https://kick.com/CabruncoGames"""
grupos_whatsapp = ["RG Tech Brasil -", "RG Tech Brasil 2 -", "PENCHINCHA"]
#grupos_whatsapp = ["Teste 01", "Teste 02"]
# Coloque a URL direta dos grupos do Facebook aqui:
grupos_facebook = ["https://www.facebook.com/cabruncogames/"] 
# Habilita ou desabilita o compartilhamento automático em grupos:
habilitar_compartilhamento_grupos = True 
# Nomes exatos dos grupos para compartilhar o post automaticamente:
compartilhar_grupos_facebook = [
    "Heroes of Might and Magic 3 Online",
    "Heroes Of Might And Magic III: Horn Of The ABYSS",
    "Heroes of Might & Magic: Olden Era"
]

# Imagem/Vídeo para o Instagram (se for vídeo curto, vira Reels):
caminho_imagem = os.path.join(os.getcwd(), "live_imagem.png")
    
# --- PARTE 1: WHATSAPP DESKTOP (RPA Simples) ---
def disparar_whatsapp():
    print("Iniciando disparo no WhatsApp...")
    
    # Copia a imagem para a área de transferência usando PowerShell
    if os.path.exists(caminho_imagem):
        comando_ps = f"""
        Add-Type -AssemblyName System.Windows.Forms
        $img = [System.Drawing.Image]::FromFile('{caminho_imagem}')
        [System.Windows.Forms.Clipboard]::SetImage($img)
        """
        subprocess.run(['powershell', '-command', comando_ps])
        print("Imagem copiada para a área de transferência.")
    else:
        print(f"⚠️ Imagem '{caminho_imagem}' não encontrada!")
    
    # O truque de mestre: forçar o Windows a chamar o WhatsApp para a frente
    os.system("start whatsapp://")
    time.sleep(5) # Aumentei o tempo de espera para o WhatsApp carregar bem
    
    for grupo in grupos_whatsapp:
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
def disparar_facebook():
    print("Iniciando disparo no Facebook...")
    
    # Cria uma pasta isolada para salvar o login do bot. Evita a falha de porta CDP.
    perfil_bot = os.path.join(os.getcwd(), "perfil_chrome_bot")
    
    with sync_playwright() as p:
        try:
            # Lança o navegador próprio em vez de tentar conectar a um Chrome existente
            context = p.chromium.launch_persistent_context(
                user_data_dir=perfil_bot,
                channel="chrome", # Usa o Google Chrome padrão
                headless=False,
                no_viewport=True
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
                                    botao_foto = page.locator("[aria-label='Foto/vídeo']").first
                                    if not botao_foto.is_visible():
                                        botao_foto = page.locator("text='Foto/vídeo'").first
                                    botao_foto.click()
                                
                                file_chooser = fc_info.value
                                file_chooser.set_files(caminho_imagem)
                                print("Imagem anexada no Facebook.")
                                page.wait_for_timeout(4000) # Aguarda upload da imagem
                            except Exception as e:
                                print(f"⚠️ Não foi possível anexar a imagem no Facebook: {e}")
                        
                        # Clica em Avançar (comentário corrigido de Publicar)
                        botao_avancar = page.locator("div[aria-label='Avançar']").first
                        if not botao_avancar.is_visible():
                            botao_avancar = page.locator("text='Avançar'").last
                        
                        botao_avancar.click()
                        page.wait_for_timeout(2000) # Aguarda popup carregar
                        
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
def disparar_instagram():
    print("Iniciando disparo no Instagram...")
    
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
                no_viewport=True,
                locale="pt-BR"
            )
            
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://www.instagram.com/")
            page.wait_for_timeout(5000)
            
            # --- PAUSA PARA LOGIN SE NECESSÁRIO ---
            if page.locator("input[name='username']").first.is_visible() or page.locator("text='Entrar'").first.is_visible():
                print("\n" + "="*60)
                print("⚠️ O INSTAGRAM ESTÁ PEDINDO LOGIN!")
                print("👉 Vá para a janela do Chrome que o bot abriu e faça o login.")
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
                botao_criar = page.locator("text='Criar'").first
                if not botao_criar.is_visible():
                    botao_criar = page.locator("text='Create'").first
                if not botao_criar.is_visible():
                    # Fallback para aria-label svg
                    botao_criar = page.locator("svg[aria-label='Nova publicação'], svg[aria-label='New post']").first
                
                botao_criar.click(timeout=10000)
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
def disparar_tiktok():
    print("Iniciando disparo no TikTok...")
    
    perfil_bot = os.path.join(os.getcwd(), "perfil_chrome_bot")
    
    if not os.path.exists(caminho_imagem):
        print(f"⚠️ ERRO: Imagem '{caminho_imagem}' não encontrada! Pulo TikTok.")
        return

    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=perfil_bot,
                channel="chrome",
                headless=False,
                no_viewport=True,
                locale="pt-BR"
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
                page.wait_for_selector("input[type='file']", timeout=15000, state="attached")
                input_file = page.locator("input[type='file']").first
                input_file.set_files(caminho_imagem)
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

# --- EXECUÇÃO ---
if __name__ == "__main__":
    # disparar_whatsapp()
    # disparar_facebook()
    disparar_instagram()
    disparar_tiktok()
    print("Automação concluída! Boa live!")