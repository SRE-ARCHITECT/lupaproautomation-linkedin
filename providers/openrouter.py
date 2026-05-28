import requests
from services.retry_handler import retry_with_backoff, is_retryable_error

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"


class OpenRouterProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str) -> str | None:
        if not self.api_key:
            return None

        try:
            print(f"[AI_PROVIDER] OpenRouter ({OPENROUTER_MODEL})...")

            def _call():
                resp = requests.post(
                    OPENROUTER_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/SRE-ARCHITECT/lupaproautomation-linkedin",
                        "X-Title": "Lupa PRO Automation"
                    },
                    json={
                        "model": OPENROUTER_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.8
                    },
                    timeout=60
                )
                data = resp.json()
                if "choices" in data and data["choices"]:
                    return data["choices"][0]["message"]["content"].strip()
                error_msg = data.get("error", {}).get("message", str(data))
                raise RuntimeError(f"OpenRouter API error: {error_msg}")

            result = retry_with_backoff(_call)
            if result:
                print(f"[SUCCESS] OpenRouter gerou conteúdo com sucesso.")
                return result
        except Exception as e:
            if is_retryable_error(e):
                print(f"[FALLBACK] OpenRouter - tentativas esgotadas.")
            else:
                print(f"[FALLBACK] OpenRouter - erro não recuperável: {str(e)[:100]}")

        return None
