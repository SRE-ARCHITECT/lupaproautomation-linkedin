import json
import os
import random
import time
import requests
from dotenv import load_dotenv

from services.ai_provider_manager import AIProviderManager
from utils.validate_buffer_payload import validate_create_post_payload

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_URL = "https://mcp.buffer.com/mcp"
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
STORY_TRACKER = os.path.join(BASE_DIR, 'post_history.txt')
USER = "SRE-ARCHITECT"
REPO = "lupaproautomation-linkedin"
BASE_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/assets"

ANGULOS = [
    "Foco na DOR DO TEMPO: Analistas de licitação perdem horas lendo diários oficiais manualmente.",
    "Foco no MEDO (FOMO): O risco de perder o maior edital do ano porque a sua equipe foi dormir ou piscou.",
    "Foco na VANTAGEM COMPETITIVA: Ser o primeiro a saber do edital e largar na frente dos concorrentes lentos.",
    "Foco FINANCEIRO: Como aumentar o lucro, vencer mais licitações e ter previsibilidade de caixa sem inchar a equipe.",
    "Foco na INOVAÇÃO: A transição de processos antigos (planilhas) para Inteligência Artificial automatizada.",
    "Foco na PRATICIDADE: O alívio de ter as melhores oportunidades mastigadas e entregues diretamente no Telegram.",
    "Foco em ESTATÍSTICA/AUTORIDADE: O volume brutal de editais no PNCP e como é impossível humano filtrar tudo."
]


def build_prompt(history: str) -> str:
    angulo = random.choice(ANGULOS)
    return f"""Você é um Copywriter de elite focado em LinkedIn Ads e Growth B2B. 
Crie uma postagem persuasiva e estratégica sobre o Lupa PRO — um radar de IA que domina o PNCP.

🔥 ÂNGULO CRIATIVO DESTA POSTAGEM:
{angulo}

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


def generate_copy() -> str:
    history = ""
    if os.path.exists(STORY_TRACKER):
        with open(STORY_TRACKER, 'r', encoding='utf-8') as f:
            history = f.read()[-2000:]

    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if not gemini_key and not groq_key and not openrouter_key:
        print("[ERROR] Nenhuma API Key de IA encontrada (GEMINI_API_KEY, GROQ_API_KEY ou OPENROUTER_API_KEY).")
        return "Erro de configuração de IA."

    manager = AIProviderManager(
        gemini_key=gemini_key,
        groq_key=groq_key,
        openrouter_key=openrouter_key
    )

    prompt = build_prompt(history)
    result = manager.generate(prompt)

    if result:
        timestamp = str(int(time.time()))[-4:]
        return f"{result}\n\n[ID:{timestamp}]"

    timestamp = str(int(time.time()))[-4:]
    fallback = f"🚀 Escalando negócios de forma inteligente com o Lupa PRO! [ID:{timestamp}]\n\n👉 Conheça: lupapro.vercel.app"
    print(f"[FALLBACK] Usando fallback estático (nenhum provider retornou conteúdo).")
    return fallback


def build_carousel_urls() -> list[str]:
    banner = f"{BASE_URL}/Banner.png"
    brand_black = f"{BASE_URL}/Screenshot_11.jpg"
    brand_white = f"{BASE_URL}/Screenshot_.jpg"

    valid_extensions = ('.jpg', '.jpeg', '.png')
    all_files = []
    if os.path.isdir(ASSETS_DIR):
        all_files = os.listdir(ASSETS_DIR)
    screenshots = [f for f in all_files if f.lower().endswith(valid_extensions)
                   and 'Screenshot_' in f
                   and f not in ['Screenshot_11.jpg', 'Screenshot_.jpg']]

    num_middle = min(len(screenshots), 2)
    middle_slides = []
    if screenshots:
        middle_slides = [f"{BASE_URL}/{img}" for img in random.sample(screenshots, num_middle)]

    urls = [banner, brand_black] + middle_slides + [brand_white]

    timestamp = str(int(time.time()))
    urls = [f"{url}?t={timestamp}" for url in urls]

    return urls[:6]


def enviar_via_mcp(texto: str, image_urls: list) -> bool:
    token = os.getenv("BUFFER_ACCESS_TOKEN")
    org_id = os.getenv("BUFFER_ORG_ID")
    channel_id = os.getenv("BUFFER_PROFILE_ID")

    if not org_id or not channel_id:
        print("[ERROR] BUFFER_ORG_ID ou BUFFER_PROFILE_ID não configurados.")
        return False

    assets = [{"image": {"url": url}} for url in image_urls]

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "create_post",
            "arguments": {
                "organizationId": org_id,
                "channelId": channel_id,
                "text": texto,
                "schedulingType": "automatic",
                "assets": assets
            }
        },
        "id": 1
    }

    valid, errors = validate_create_post_payload(payload)
    if not valid:
        print(f"[ERROR] Payload inválido: {'; '.join(errors)}")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    try:
        print(f"[BUFFER] Enviando para Org: {org_id} | Canal: {channel_id} | {len(assets)} imagem(ns)")
        response = requests.post(MCP_URL, headers=headers, json=payload, timeout=30)
        print(f"[MCP] Status Code: {response.status_code}")

        raw_text = response.text
        try:
            if "data: {" in raw_text:
                json_str = raw_text.split("data: ", 1)[1].strip()
                resp_json = json.loads(json_str)
            else:
                resp_json = response.json()

            if "error" in resp_json:
                print(f"[ERROR] MCP: {resp_json['error']}")
                return False

            if "result" in resp_json and resp_json["result"].get("isError"):
                content = resp_json["result"].get("content", [])
                print(f"[ERROR] MCP tool error: {content}")
                return False

            print(f"[SUCCESS] Post agendado no Buffer.")
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Falha ao processar resposta MCP: {e}")
            print(f"[MCP] Resposta bruta: {raw_text[:500]}")
            return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Falha na requisição MCP: {e}")
        return False


def main():
    print("=" * 50)
    print("[AI_PROVIDER] Iniciando geração de conteúdo...")
    copy = generate_copy()

    if copy:
        with open(STORY_TRACKER, 'a', encoding='utf-8') as f:
            f.write(f"\n---\n{copy}")

    urls = build_carousel_urls()

    if not os.getenv("BUFFER_ACCESS_TOKEN"):
        print("[BUFFER] DRY RUN - Token não encontrado. Modo de simulação.")
        print(f"[BUFFER] Texto:\n{copy}")
        print(f"[BUFFER] Imagens ({len(urls)}):\n" + "\n".join(urls))
        return

    print(f"[BUFFER] Agendando post com {len(urls)} imagem(ns)...")
    if enviar_via_mcp(copy, urls):
        print("[SUCCESS] Postagem concluída com sucesso!")
    else:
        print("[ERROR] Falha na postagem. Verifique os logs.")


if __name__ == "__main__":
    main()
