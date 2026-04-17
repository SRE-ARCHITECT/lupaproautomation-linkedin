import json
import os
import random
import time
import requests
from google import genai
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

    # Validação de Segurança: Credenciais Críticas
    if not gemini_key and not groq_key:
        print("❌ ERRO CRÍTICO: Nenhuma API Key de IA encontrada (GEMINI_API_KEY ou GROQ_API_KEY).")
        return "Erro de configuração de IA."

    prompt = f"""Você é um Copywriter de elite focado em LinkedIn Ads e Growth B2B. 
Crie uma postagem persuasiva e estratégica sobre o Lupa PRO — um radar de IA que domina o PNCP.

PÚBLICO-ALVO: Empresários, Analistas de Licitação e Diretores Comerciais.
OBJETIVO: Autoridade e Conversão.

ESTRUTURA DE COPY (Use PAS ou AIDA alternadamente):
1. GANCHO (HOOK): Uma frase curta e cortante que pare o scroll. Foque em lucro perdido, eficiência ou futuro.
2. PROBLEMA: A dificuldade de encontrar editais relevantes no mar de dados do PNCP.
3. AGITAÇÃO: O risco de perder contratos milionários por falta de monitoramento 24h.
4. SOLUÇÃO: Como a IA do Lupa PRO entrega a oportunidade "mastigada" no Telegram.
5. CTA: Convite magnético para clicar em lupapro.vercel.app

DIRETRIZES RÍGIDAS:
- Tom: Visionário, direto e ultra-profissional.
- Formatação: Use parágrafos curtos (máximo 2 linhas) e listas de benefícios.
- Restrição: NUNCA repita nada de: {history}
- Obrigatoriedade: Link lupapro.vercel.app e emojis sóbrios (🚀, 📈, 🛡️, 👁️).
- Hashtags: 3 a 5 ao final, focadas em #PNCP, #Licitações, #SaaS, #InteligênciaArtificial.

Retorne APENAS o texto da copy, formatado para LinkedIn."""

    # TENTATIVA 1: Gemini 2.0
    try:
        if gemini_key:
            print("🤖 Tentando Gemini 2.0 Flash...")
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            return response.text.strip()
    except Exception as e:
        print(f"⚠️ Gemini 2.0 falhou: {e}")

    # TENTATIVA 2: Gemini 1.5
    try:
        if gemini_key:
            print("🤖 Tentando Gemini 1.5 Flash (Fallback)...")
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            return response.text.strip()
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
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8
                }
            )
            data = response.json()
            if "choices" in data:
                return data['choices'][0]['message']['content'].strip()
            else:
                print(f"⚠️ Erro Groq API: {data.get('error')}")
    except Exception as e:
        print(f"❌ Falha técnica Groq: {e}")
    
    return "🚀 Escalando negócios com o Lupa PRO! 👉 lupapro.vercel.app"

def enviar_via_mcp(texto: str, image_urls: list) -> bool:
    token = os.getenv("BUFFER_ACCESS_TOKEN")
    org_id = os.getenv("BUFFER_ORG_ID")
    channel_id = os.getenv("BUFFER_PROFILE_ID")

    if not org_id or not channel_id:
        print("❌ ERRO: BUFFER_ORG_ID ou BUFFER_PROFILE_ID não configurados.")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    arguments = {
        "organizationId": org_id,
        "channelId": channel_id,
        "text": texto,
        "schedulingType": "automatic", # Isso joga o post para o próximo slot da fila (Queue)
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
        print(f"📤 [DEBUG] Enviando para Org: {org_id} | Canal: {channel_id}")
        response = requests.post(MCP_URL, headers=headers, json=payload, timeout=30)
        
        print(f"📡 [DEBUG] Status Code: {response.status_code}")
        
        # Buffer MCP retorna SSE (Server-Sent Events) no formato "data: {...}"
        raw_text = response.text
        try:
            # Tenta extrair o JSON se a resposta vier como "data: {"
            if "data: {" in raw_text:
                json_str = raw_text.split("data: ", 1)[1].strip()
                resp_json = json.loads(json_str)
            else:
                resp_json = response.json()
            
            print(f"📝 [DEBUG] Resposta Processada: {json.dumps(resp_json, indent=2)}")
            
            if "error" in resp_json:
                print(f"❌ [AI ERROR] {resp_json['error']}")
                return False
            
            if "result" in resp_json and resp_json["result"].get("isError"):
                content = resp_json["result"].get("content", [])
                print(f"❌ [TOOL ERROR] Detalhes: {content}")
                return False

            return response.status_code == 200
        except Exception as e:
            print(f"⚠️ Erro ao processar resposta da API: {e}")
            print(f"📝 Bruto: {raw_text[:500]}")
            return response.status_code == 200
    except Exception as e:
        print(f"❌ [EXCEPTION] Erro na requisição: {e}")
        return False

def main():
    # 1. Gerar Texto Único
    print("🤖 Gerando conteúdo inédito com IA...")
    copy = get_unique_copy()
    
    # 2. Salvar histórico para não repetir
    if copy:
        with open(STORY_TRACKER, 'a', encoding='utf-8') as f:
            f.write(f"\n---\n{copy}")
    
    # 3. Definir URLs das imagens (Estratégia Premium)
    USER = "SRE-ARCHITECT"
    REPO = "lupaproautomation-linkedin"
    BASE_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/assets"
    
    # Imagens Fixas de Branding (Obrigatórias)
    banner = f"{BASE_URL}/Banner.png"
    brand_black = f"{BASE_URL}/Screenshot_11.jpg"
    brand_white = f"{BASE_URL}/Screenshot_.jpg"
    
    # Detecta capturas de tela disponíveis para o miolo do carrossel
    valid_extensions = ('.jpg', '.jpeg', '.png')
    all_files = os.listdir(ASSETS_DIR)
    screenshots = [f for f in all_files if f.lower().endswith(valid_extensions) and 'Screenshot_' in f 
                   and f not in ['Screenshot_11.jpg', 'Screenshot_.jpg']]
    
    # Montagem Estratégica:
    # 1. Slide de Gancho (Banner)
    # 2. Slide de Branding Black
    # 3. Slides de Prova Social/Sistema (2-3 aleatórios)
    # 4. Slide de Fechamento/CTA (Branding White)
    
    num_middle = min(len(screenshots), 2)
    middle_slides = [f"{BASE_URL}/{img}" for img in random.sample(screenshots, num_middle)]
    
    urls = [banner, brand_black] + middle_slides + [brand_white]
    
    # Limitação do LinkedIn: Recomendado no máximo 5-7 imagens para Buffer
    urls = urls[:6]
    
    # 4. Enviar para o Buffer
    if not os.getenv("BUFFER_ACCESS_TOKEN"):
        print("🚨 AVISO: BUFFER_ACCESS_TOKEN não encontrado. Rodando em modo DRY RUN (apenas log).")
        print(f"📝 TEXTO QUE SERIA POSTADO:\n{copy}")
        print(f"🖼️ URLS DAS IMAGENS:\n{urls}")
        return

    print(f"📤 Agendando no Buffer com {len(urls)} imagens...")
    if enviar_via_mcp(copy, urls):
        print("✅ Sucesso! Post agendado na fila do Buffer.")
    else:
        print("❌ Falha no agendamento. Verifique os logs da API.")

if __name__ == "__main__":
    main()
