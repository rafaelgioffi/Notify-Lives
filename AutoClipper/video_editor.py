import ffmpeg
import os

def extract_audio(video_path, output_audio_path):
    """Extrai o áudio do vídeo para análise rápida pela IA."""
    try:
        print(f"Extraindo áudio de {video_path}...")
        (
            ffmpeg
            .input(video_path)
            .output(output_audio_path, acodec='libmp3lame', q=4, loglevel='error')
            .overwrite_output()
            .run()
        )
        print("Áudio extraído com sucesso.")
        return True
    except ffmpeg.Error as e:
        print(f"Erro ao extrair áudio: {e}")
        return False

def create_vertical_clip(video_path, start_time, end_time, output_clip_path):
    """
    Corta o vídeo e transforma o 16:9 em 9:16 (vertical) com fundo desfocado.
    Perfeito para YouTube Shorts, Instagram Reels e TikTok.
    """
    try:
        print(f"Criando clipe vertical de {start_time} até {end_time}...")
        
        # Carrega o vídeo original no tempo especificado
        video = ffmpeg.input(video_path, ss=start_time, to=end_time)
        
        # Pega a faixa de áudio original
        audio = video.audio
        
        # Cria o fundo desfocado (escala para preencher a altura 1920 e desfoca)
        blurred_bg = (
            video.video
            .filter('scale', 1080, 1920, force_original_aspect_ratio='increase')
            .filter('crop', 1080, 1920)
            .filter('boxblur', 20)
        )
        
        # Escala o vídeo original para caber na largura 1080
        foreground = (
            video.video
            .filter('scale', 1080, -1)
        )
        
        # Sobrepõe o vídeo original centralizado no fundo desfocado
        final_video = ffmpeg.overlay(blurred_bg, foreground, x='(W-w)/2', y='(H-h)/2')
        
        # Junta vídeo editado e áudio original
        (
            ffmpeg
            .output(final_video, audio, output_clip_path, vcodec='libx264', acodec='aac', preset='fast', loglevel='error')
            .overwrite_output()
            .run()
        )
        print(f"Clipe vertical gerado: {output_clip_path}")
        return True
        
    except ffmpeg.Error as e:
        print(f"Erro ao processar vídeo: {e}")
        return False
