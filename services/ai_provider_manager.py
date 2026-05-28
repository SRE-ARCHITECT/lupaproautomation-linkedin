from providers.gemini import GeminiProvider
from providers.groq import GroqProvider
from providers.openrouter import OpenRouterProvider


class AIProviderManager:
    def __init__(self, gemini_key: str = None, groq_key: str = None, openrouter_key: str = None):
        self.providers = []
        if gemini_key:
            self.providers.append(("Gemini", GeminiProvider(gemini_key)))
        if groq_key:
            self.providers.append(("Groq", GroqProvider(groq_key)))
        if openrouter_key:
            self.providers.append(("OpenRouter", OpenRouterProvider(openrouter_key)))

    def generate(self, prompt: str) -> str | None:
        for name, provider in self.providers:
            print(f"[AI_PROVIDER] Tentando provider: {name}")
            result = provider.generate(prompt)
            if result:
                return result
            print(f"[FALLBACK] {name} não retornou resultado. Provider seguinte...")
        return None
