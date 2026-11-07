import os
import time
from google import genai
from dotenv import load_dotenv

# Carrega variáveis de ambiente (API Key)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def analyze_audio_for_clips(audio_path):
    """
    Faz o upload do áudio para o Gemini 2.5 Flash e pede para encontrar 
    os melhores momentos baseados em empolgação, gritos, risadas ou momentos épicos.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "sua_chave_aqui":
        print("ERRO: GEMINI_API_KEY não configurada no .env!")
        return []

    client = genai.Client(api_key=GEMINI_API_KEY)

    print(f"Fazendo upload do áudio {audio_path} para o Google Gemini...")
    try:
        audio_file = client.files.upload(file=audio_path)
        print("Upload concluído. Aguardando processamento...")
        
        # O Gemini pode levar uns segundos para processar o áudio no servidor
        time.sleep(10)
        
        prompt = (
            "Você é um editor de vídeos profissional focando em cortes virais para TikTok e Shorts. "
            "Ouça este áudio de uma gameplay (Heroes of Might and Magic) e identifique de 1 a 3 "
            "momentos de altíssima emoção, empolgação, susto, risada ou narrativa interessante. "
            "Retorne APENAS uma lista no formato exato (sem texto extra, markdown ou explicações): "
            "start_time - end_time "
            "Exemplo: "
            "00:01:20 - 00:02:10 "
            "00:05:40 - 00:06:15 "
            "Faça os clipes terem entre 30 a 59 segundos no máximo."
        )

        print("Iniciando análise (isso pode demorar dependendo do tamanho do áudio)...")
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                audio_file,
                prompt
            ]
        )
        
        print("Análise concluída!")
        print("Resposta bruta da IA:\n", response.text)
        
        # Parse da resposta para pegar os tempos
        clips = []
        for line in response.text.strip().split('\n'):
            line = line.strip()
            if '-' in line and ':' in line:
                try:
                    parts = line.split('-')
                    start = parts[0].strip()
                    end = parts[1].strip()
                    clips.append((start, end))
                except:
                    continue
                    
        # Apaga o arquivo do servidor do Google para não consumir cota de armazenamento
        client.files.delete(name=audio_file.name)
        
        return clips

    except Exception as e:
        print(f"Erro na análise de IA: {e}")
        return []
