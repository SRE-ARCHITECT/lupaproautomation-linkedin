import requests
from services.retry_handler import retry_with_backoff, is_retryable_error

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


class GroqProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str) -> str | None:
        if not self.api_key:
            return None

        try:
            print(f"[AI_PROVIDER] Groq ({GROQ_MODEL})...")

            def _call():
                resp = requests.post(
                    GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": GROQ_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.8
                    },
                    timeout=60
                )
                data = resp.json()
                if "choices" in data and data["choices"]:
                    return data["choices"][0]["message"]["content"].strip()
                error_msg = data.get("error", {}).get("message", str(data))
                raise RuntimeError(f"Groq API error: {error_msg}")

            result = retry_with_backoff(_call)
            if result:
                print(f"[SUCCESS] Groq gerou conteúdo com sucesso.")
                return result
        except Exception as e:
            if is_retryable_error(e):
                print(f"[FALLBACK] Groq - tentativas esgotadas.")
            else:
                print(f"[FALLBACK] Groq - erro não recuperável: {str(e)[:100]}")

        return None
