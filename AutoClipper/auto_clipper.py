import os
import time
import psutil
import ctypes
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configurações
WATCH_DIR = r"C:\OneDrive\Vídeos\HOMM_OE"
DONE_DIR = os.path.join(WATCH_DIR, "Processados")
CLIPS_DIR = os.path.join(WATCH_DIR, "Clipes")

# Cria pastas se não existirem
os.makedirs(DONE_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)

def is_fullscreen_app_running():
    """
    Verifica se o aplicativo atualmente em foco no Windows está em tela cheia.
    Usado para evitar rodar o processamento pesado de IA/FFmpeg enquanto o usuário joga.
    """
    try:
        user32 = ctypes.windll.user32
        # Pega a resolução da tela principal
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        
        # Pega o handle da janela atual em foco
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
            
        # Pega o tamanho da janela
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        
        # Se o tamanho da janela for igual ou maior que a tela, está em fullscreen
        if width >= screen_width and height >= screen_height:
            # Pode ser o desktop, mas na dúvida pausamos.
            return True
        return False
    except Exception as e:
        print(f"Erro ao verificar fullscreen: {e}")
        return False

class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.mp4', '.mkv')):
            print(f"Novo vídeo detectado: {event.src_path}")
            self.process_video_when_ready(event.src_path)

    def process_video_when_ready(self, filepath):
        print(f"Aguardando a gravação terminar: {filepath}")
        # Espera o tamanho do arquivo parar de crescer (indicando que o OBS terminou)
        last_size = -1
        while True:
            try:
                current_size = os.path.getsize(filepath)
                if current_size == last_size and current_size > 0:
                    break
                last_size = current_size
            except FileNotFoundError:
                return
            time.sleep(5)
            
        print("Gravação concluída. Aguardando o PC ficar ocioso...")
        
        # Aguarda não ter app em fullscreen
        while is_fullscreen_app_running():
            print("Jogo em tela cheia detectado. Pausando processamento...")
            time.sleep(60)
            
        print("PC ocioso! Iniciando extração e análise de IA...")
        self.run_clipper_pipeline(filepath)
        
    def run_clipper_pipeline(self, filepath):
        import video_editor
        import ai_analyzer
        
        print(f"Iniciando processamento de {filepath}...")
        
        # 1. Extrai Áudio
        filename = os.path.basename(filepath)
        name_only = os.path.splitext(filename)[0]
        audio_path = os.path.join(WATCH_DIR, f"{name_only}_temp_audio.mp3")
        
        if not video_editor.extract_audio(filepath, audio_path):
            return
            
        # 2. Analisa com Gemini
        clips_timestamps = ai_analyzer.analyze_audio_for_clips(audio_path)
        
        # 3. Corta e cria os verticais
        if not clips_timestamps:
            print("Nenhum momento épico encontrado pela IA.")
        else:
            for idx, (start, end) in enumerate(clips_timestamps):
                output_clip = os.path.join(CLIPS_DIR, f"{name_only}_clip{idx+1}.mp4")
                video_editor.create_vertical_clip(filepath, start, end, output_clip)
                # Opcional: aqui poderíamos chamar o módulo de Publicação para subir o clip
                # e apagar o clipe se sucesso.
                
        # Limpeza do áudio temporário
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
        # Move o original para processados
        final_path = os.path.join(DONE_DIR, filename)
        os.rename(filepath, final_path)
        print(f"Vídeo {filename} finalizado com sucesso!")

def start_watching():
    print(f"Iniciando monitoramento da pasta: {WATCH_DIR}")
    event_handler = VideoHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watching()
