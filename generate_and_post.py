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

    prompt = f"""Você é um copywriter sênior especializado em licenciamento público e B2B SaaS. 
Crie uma postagens de autoridade para o LinkedIn sobre o radar de licitações Lupa PRO.
O Lupa PRO usa IA para varrer o PNCP e entregar oportunidades milionárias direto no Telegram dos assinantes.

DIRETRIZES DE ESTILO:
- Tom de voz: Profissional, visionário e focado em lucro/escala.
- Gatilhos: Autoridade, Eficiência (IA) e Escassez (não perder prazos).
- Estrutura: Gancho impactante -> Problema/Oportunidade -> Solução (Lupa PRO) -> CTA.

REGRAS RÍGIDAS:
1. NUNCA repita ou use ideias similares a: {history}
2. Link obrigatório: lupapro.vercel.app
3. Use emojis de forma elegante (não exagere).
4. Termine com 3 a 5 hashtags estratégicas.
Retorne APENAS o texto da postagem (copy)."""

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
    org_id = os.getenv("BUFFER_ORG_ID", "6976908d2cfaeb9054bda013")
    channel_id = os.getenv("BUFFER_PROFILE_ID", "6976915b31b76c40caf9a9be")

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
        try:
            resp_json = response.json()
            print(f"📝 [DEBUG] Resposta Completa: {json.dumps(resp_json, indent=2)}")
            
            # Verifica erros no nível do JSON-RPC ou da ferramenta
            if "error" in resp_json:
                print(f"❌ [AI ERROR] {resp_json['error']}")
                return False
            
            if "result" in resp_json and resp_json["result"].get("isError"):
                print(f"❌ [TOOL ERROR] Detalhes: {resp_json['result'].get('content')}")
                return False

            return response.status_code == 200
        except:
            print(f"⚠️ Resposta não é JSON: {response.text[:500]}")
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
    
    # 3. Definir URLs das imagens (Raw GitHub)
    USER = "SRE-ARCHITECT"
    REPO = "lupaproautomation-linkedin"
    
    # Detecta imagens disponíveis na pasta assets
    valid_extensions = ('.jpg', '.jpeg', '.png')
    available_images = [f for f in os.listdir(ASSETS_DIR) if f.lower().endswith(valid_extensions) and 'Screenshot' in f]
    
    if not available_images:
        print("⚠️ Nenhuma imagem de Screenshot encontrada em assets/. Usando imagem padrão.")
        urls = [f"https://raw.githubusercontent.com/{USER}/{REPO}/main/assets/Banner.png"]
    else:
        # Sorteia 3 a 5 screenshots para o carrossel (ou o máximo disponível)
        num_to_pick = min(len(available_images), random.randint(3, 5))
        picked_images = random.sample(available_images, num_to_pick)
        urls = [f"https://raw.githubusercontent.com/{USER}/{REPO}/main/assets/{img}" for img in picked_images]
    
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
