import pyautogui
import time
import os
import pyperclip
from playwright.sync_api import sync_playwright

# --- CONFIGURAÇÕES ---
mensagem = """Fala galera! Tudo bem com vcs? Estamos ao vivo jogando Heroes Olden Era!
O melhor conteúdo sobre HOMM:OE do Brasil!

Cola lá:
🟣 https://twitch.tv/CabruncoGamesBR
🟢 https://kick.com/CabruncoGames"""
# grupos_whatsapp = ["RG Tech Brasil", "RG Tech Brasil 2"]
grupos_whatsapp = ["Teste 01", "Teste 02"]
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
    
# --- PARTE 1: WHATSAPP DESKTOP (RPA Simples) ---
def disparar_whatsapp():
    print("Iniciando disparo no WhatsApp...")
    
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
        
        # Solução para mensagens incompletas e rápidas: Copiar e Colar
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

# --- EXECUÇÃO ---
if __name__ == "__main__":
    disparar_whatsapp()
    disparar_facebook()
    print("Automação concluída! Boa live!")