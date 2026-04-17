import json
import os
import random
import time
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_URL = "https://mcp.buffer.com/mcp"
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
STORY_TRACKER = os.path.join(BASE_DIR, 'post_history.txt')

def get_unique_copy():
    """Usa o Gemini para gerar uma copy de vendas inédita."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "🚨 Lupa PRO: Licitações Milionárias na sua mão! 👉 lupapro.vercel.app"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    # Busca histórico para evitar repetição
    history = ""
    if os.path.exists(STORY_TRACKER):
        with open(STORY_TRACKER, 'r', encoding='utf-8') as f:
            history = f.read()[-2000:] # Pega os últimos caracteres

    prompt = f"""Você é um copywriter de elite especialista em B2B e Licitações Públicas (PNCP).
Sua missão: Escrever uma postagem curta e impactante para o LinkedIn sobre o SaaS Lupa PRO.

O Lupa PRO é um radar de IA que encontra editais milionários antes da concorrência e envia pro Telegram.

REGRAS:
1. NUNCA repita frases ou chamadas usadas anteriormente: {history}
2. Varie o tom: às vezes urgente, às vezes técnico, às vezes focado em lucro, às vezes em produtividade.
3. Use emojis de forma elegante.
4. Mencione o link: lupapro.vercel.app
5. Hashtags variadas (5 a 8) no final.
6. Comece com uma "Headline" matadora em caps lock.

Retorne APENAS o texto da postagem."""

    try:
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Salva no histórico
        with open(STORY_TRACKER, 'a', encoding='utf-8') as f:
            f.write(f"\n---\n{content[:100]}")
            
        return content
    except Exception as e:
        print(f"❌ Erro na IA: {e}")
        return "🚀 Descubra licitações milionárias com o Lupa PRO! 👉 lupapro.vercel.app"

def enviar_via_mcp(texto: str, image_urls: list) -> bool:
    token = os.getenv("BUFFER_ACCESS_TOKEN")
    org_id = os.getenv("BUFFER_ORG_ID", "6976908d2cfaeb9054bda013")
    channel_id = os.getenv("BUFFER_PROFILE_ID", "6976915b31b76c40caf9a9be")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    arguments = {
        "organizationId": org_id,
        "channelId": channel_id,
        "text": texto,
        "schedulingType": "automatic",
        "assets": {
            "images": [{"url": url} for url in image_urls]
        }
    }
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "create_post",
            "arguments": arguments
        },
        "id": 1
    }

    try:
        response = requests.post(MCP_URL, headers=headers, json=payload, timeout=30)
        return response.status_code == 200
    except:
        return False

def main():
    # 1. Gerar Texto Único
    print("🤖 Gerando conteúdo inédito com IA...")
    copy = get_unique_copy()
    
    # 2. Definir URLs das imagens (Raw GitHub)
    # ATENÇÃO: Após criar seu repo, altere o link abaixo para o seu usuário
    USER = "SRE-ARCHITECT"
    REPO = "lupaproautomation-linkedin"
    
    # Sorteia 3 a 5 screenshots para o carrossel
    img_nums = random.sample(range(1, 11), random.randint(3, 5))
    urls = [f"https://raw.githubusercontent.com/{USER}/{REPO}/main/assets/Screenshot_{n}.jpg" for n in img_nums]
    
    print(f"📤 Agendando no Buffer com {len(urls)} imagens...")
    if enviar_via_mcp(copy, urls):
        print("✅ Sucesso! Post agendado.")
    else:
        print("❌ Falha no agendamento.")

if __name__ == "__main__":
    main()
