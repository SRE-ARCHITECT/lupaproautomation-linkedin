from google import genai
from services.retry_handler import retry_with_backoff, is_retryable_error

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
]


class GeminiProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key) if api_key else None

    def generate(self, prompt: str) -> str | None:
        if not self.client:
            return None

        for model_name in GEMINI_MODELS:
            try:
                print(f"[AI_PROVIDER] Gemini ({model_name})...")

                def _call(m=model_name, p=prompt):
                    response = self.client.models.generate_content(model=m, contents=p)
                    return response.text.strip() if response and response.text else None

                result = retry_with_backoff(_call)
                if result:
                    print(f"[SUCCESS] Gemini ({model_name}) gerou conteúdo com sucesso.")
                    return result
            except Exception as e:
                if is_retryable_error(e):
                    print(f"[FALLBACK] Gemini ({model_name}) - tentativas esgotadas.")
                else:
                    print(f"[FALLBACK] Gemini ({model_name}) - erro não recuperável: {str(e)[:100]}")
                continue

        return None
