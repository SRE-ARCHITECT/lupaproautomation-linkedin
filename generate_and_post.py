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
    """Gera copy inédita com Fallback: Gemini 2.0 -> Gemini 1.5 -> Groq."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    # Busca histórico
    history = ""
    if os.path.exists(STORY_TRACKER):
        with open(STORY_TRACKER, 'r', encoding='utf-8') as f:
            history = f.read()[-2000:]

    prompt = f"""Você é um copywriter sênior. Crie uma postagem curta e impactante para o LinkedIn sobre o SaaS Lupa PRO.
O Lupa PRO é um radar de IA que encontra editais milionários do PNCP e envia para o Telegram.
REGRAS:
1. NUNCA repita: {history}
2. Mencione: lupapro.vercel.app
3. Hashtags variadas no final.
PRECISE SER CRIATIVO E VARIAR O TEMA (Lucro, Tempo, Concorrência, Tecnologia).
Retorne APENAS o texto da postagem."""

    # TENTATIVA 1: Gemini 2.0
    try:
        print("🤖 Tentando Gemini 2.0 Flash...")
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        return model.generate_content(prompt).text.strip()
    except Exception as e:
        print(f"⚠️ Gemini 2.0 falhou: {e}")

    # TENTATIVA 2: Gemini 1.5
    try:
        print("🤖 Tentando Gemini 1.5 Flash (Fallback)...")
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model.generate_content(prompt).text.strip()
    except Exception as e:
        print(f"⚠️ Gemini 1.5 falhou: {e}")

    # TENTATIVA 3: Groq (Llama 3)
    try:
        if groq_key:
            print("🤖 Tentando Groq Llama-3 (Fallback Final)...")
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8
                }
            )
            return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"❌ Todas as IAs falharam: {e}")
    
    return "📈 Escalando negócios com o Lupa PRO! 👉 lupapro.vercel.app"

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
