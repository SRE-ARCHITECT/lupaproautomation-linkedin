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

    angulos = [
        "Foco na DOR DO TEMPO: Analistas de licitação perdem horas lendo diários oficiais manualmente.",
        "Foco no MEDO (FOMO): O risco de perder o maior edital do ano porque a sua equipe foi dormir ou piscou.",
        "Foco na VANTAGEM COMPETITIVA: Ser o primeiro a saber do edital e largar na frente dos concorrentes lentos.",
        "Foco FINANCEIRO: Como aumentar o lucro, vencer mais licitações e ter previsibilidade de caixa sem inchar a equipe.",
        "Foco na INOVAÇÃO: A transição de processos antigos (planilhas) para Inteligência Artificial automatizada.",
        "Foco na PRATICIDADE: O alívio de ter as melhores oportunidades mastigadas e entregues diretamente no Telegram.",
        "Foco em ESTATÍSTICA/AUTORIDADE: O volume brutal de editais no PNCP e como é impossível humano filtrar tudo."
    ]
    angulo_sorteado = random.choice(angulos)

    prompt = f"""Você é um Copywriter de elite focado em LinkedIn Ads e Growth B2B. 
Crie uma postagem persuasiva e estratégica sobre o Lupa PRO — um radar de IA que domina o PNCP.

🔥 ÂNGULO CRIATIVO DESTA POSTAGEM:
{angulo_sorteado}

PÚBLICO-ALVO: Empresários, Analistas de Licitação e Diretores Comerciais.
OBJETIVO: Autoridade e Conversão.

ESTRUTURA DE COPY (Seja fluido e natural, adapte a estrutura PAS ou AIDA para focar no Ângulo Criativo acima):
1. GANCHO (HOOK): Uma frase inicial chocante, provocativa ou com uma pergunta forte baseada no ângulo sorteado.
2. CONTEXTO/PROBLEMA: Desenvolva o problema principal associado ao ângulo.
3. SOLUÇÃO/TECNOLOGIA: Como o Lupa PRO (IA + PNCP + Telegram) resolve isso de forma elegante.
4. CTA: Convite sutil e magnético para testar no lupapro.vercel.app

DIRETRIZES RÍGIDAS DE VARIAÇÃO:
- Mude o vocabulário, não use sempre as mesmas palavras ("dificuldade", "mar de dados", "risco"). Varie muito!
- Formatação: Use parágrafos curtos, mas varie a forma visual (use listas, pequenos insights, etc).
- Restrição: NUNCA repita nada da estrutura e palavras do histórico: {history}
- Obrigatoriedade: O link exato lupapro.vercel.app e emojis adequados ao tom.
- Hashtags: 3 a 5 focadas no nicho (#PNCP, #Licitações, #B2B, #SaaS).

Retorne APENAS o texto final do post para o LinkedIn."""

    # TENTATIVA 1: Gemini 2.0
    try:
        if gemini_key:
            print("🤖 Tentando Gemini 2.0 Flash...")
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            timestamp = str(int(time.time()))[-4:]
            return f"{response.text.strip()}\n\n[ID:{timestamp}]"
    except Exception as e:
        print(f"⚠️ Gemini 2.0 falhou: {e}")

    # TENTATIVA 2: Gemini 1.5
    try:
        if gemini_key:
            print("🤖 Tentando Gemini 1.5 Flash (Fallback)...")
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            timestamp = str(int(time.time()))[-4:]
            return f"{response.text.strip()}\n\n[ID:{timestamp}]"
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
                timestamp = str(int(time.time()))[-4:]
                return f"{data['choices'][0]['message']['content'].strip()}\n\n[ID:{timestamp}]"
            else:
                print(f"⚠️ Erro Groq API: {data.get('error')}")
    except Exception as e:
        print(f"❌ Falha técnica Groq: {e}")
    
    # Se tudo falhar, gera um fallback único para não ser bloqueado por duplicidade no Buffer
    timestamp = str(int(time.time()))[-4:]
    return f"🚀 Escalando negócios de forma inteligente com o Lupa PRO! [ID:{timestamp}]\n\n👉 Conheça: lupapro.vercel.app"

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
    
    # Adicionar timestamp nas URLs para burlar o detector de duplicidade de mídia do Buffer
    timestamp = str(int(time.time()))
    urls = [f"{url}?t={timestamp}" for url in urls]
    
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
