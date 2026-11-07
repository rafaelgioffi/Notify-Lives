import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY or GEMINI_API_KEY == "sua_chave_aqui":
    print("ERRO: Chave da API não encontrada no .env")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

try:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents='Responda com OK se você estiver recebendo esta mensagem.'
    )
    print(f"Sucesso! Resposta da API: {response.text}")
except Exception as e:
    print(f"Erro ao conectar com a API: {e}")
