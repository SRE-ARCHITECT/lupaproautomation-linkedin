# Blueprint Técnico — Automação LinkedIn Lupa PRO v2.0

---

## 1. Diagrama de Camadas

```txt
┌─────────────────────────────────────────────────────┐
│                   GitHub Actions                     │
│              daily_post.yml (cron 13:00 UTC)         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              generate_and_post.py                    │
│                  Entry Point                         │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ generate_   │  │ build_       │  │ enviar_    │ │
│  │ copy()      │  │ carousel_    │  │ via_mcp()  │ │
│  │             │  │ urls()       │  │            │ │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘ │
└─────────┼────────────────┼────────────────┼────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────┐ ┌──────────┐ ┌──────────────────┐
│ AIProvider      │ │ Assets   │ │ Payload          │
│ Manager         │ │ Builder  │ │ Validation       │
├─────────────────┤ ├──────────┤ ├──────────────────┤
│ Orquestra       │ │ Banner   │ │ validate_create_ │
│ providers       │ │ + Brand  │ │ post_payload()   │
│ com fallback    │ │ + Randos │ │                  │
└────────┬────────┘ └──────────┘ └──────────────────┘
         │
    ┌────┴────────┬───────────┬──────────────┐
    ▼             ▼           ▼              ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Gemini │ │ Groq     │ │OpenRouter│ │ Static       │
│ 2.5    │ │ Llama 3  │ │ Llama 3  │ │ Fallback     │
│ Flash  │ │ 70B      │ │ 70B      │ │              │
├────────┤ ├──────────┤ ├──────────┤ ├──────────────┤
│ Retry  │ │ Retry    │ │ Retry    │ │ Sempre OK    │
│ 5/15/30│ │ 5/15/30  │ │ 5/15/30  │ │              │
└────────┘ └──────────┘ └──────────┘ └──────────────┘
```

---

## 2. Módulos e Responsabilidades

### 2.1 `services/retry_handler.py`

**Responsabilidade:** Executar função com retry e backoff.

**API Pública:**
```python
def retry_with_backoff(func, *args, **kwargs)
def is_retryable_error(error: Exception) -> bool
```

**Constantes:**
```python
RETRY_DELAYS = [5, 15, 30]  # segundos
RETRYABLE_KEYWORDS = ["429", "resource_exhausted", "timeout", "rate limit", ...]
```

**Fluxo:**
1. Tenta executar `func`
2. Se sucesso → retorna resultado
3. Se erro recuperável → aguarda delay com jitter, retenta
4. Se erro não recuperável → propaga exceção imediatamente
5. Após 3 tentativas → propaga exceção

### 2.2 `services/quota_manager.py`

**Responsabilidade:** Controlar taxa de requests.

**API Pública:**
```python
class QuotaManager:
    def __init__(self, max_per_minute=5, min_delay_seconds=12.0)
    def wait_if_needed(self)
```

**Algoritmo:**
```python
# A cada chamada de wait_if_needed():
1. Remove timestamps expirados (>60s)
2. Se atingiu max_per_minute → aguarda até janela abrir
3. Se não respeitou min_delay → aguarda diferença
4. Registra timestamp atual
```

### 2.3 `services/ai_provider_manager.py`

**Responsabilidade:** Orquestrar providers com fallback.

**API Pública:**
```python
class AIProviderManager:
    def __init__(self, gemini_key, groq_key, openrouter_key)
    def generate(self, prompt: str) -> str | None
```

**Fluxo:**
```python
for name, provider in self.providers:
    result = provider.generate(prompt)
    if result:
        return result
return None  # aciona static fallback
```

### 2.4 `providers/gemini.py`

**Provider:** Google Gemini via SDK `google.genai`

**Modelos (em ordem):**
1. `gemini-2.5-flash`
2. `gemini-2.0-flash-lite`

**Erros recuperáveis:** 429, timeout, quota
**Erros não recuperáveis:** 400 (API key inválida), 404 (modelo não encontrado)

### 2.5 `providers/groq.py`

**Provider:** Groq Cloud via REST API

**Endpoint:** `POST https://api.groq.com/openai/v1/chat/completions`
**Modelo:** `llama-3.3-70b-versatile`
**Timeouts:** 60s

### 2.6 `providers/openrouter.py`

**Provider:** OpenRouter via REST API

**Endpoint:** `POST https://openrouter.ai/api/v1/chat/completions`
**Modelo:** `meta-llama/llama-3.3-70b-instruct`
**Headers especiais:** `HTTP-Referer`, `X-Title`

### 2.7 `utils/validate_buffer_payload.py`

**Responsabilidade:** Validar payload antes do envio ao MCP.

**Regras de validação:**
- `params.name` deve ser `"create_post"`
- `arguments.organizationId` obrigatório
- `arguments.channelId` obrigatório
- `arguments.text` obrigatório
- `arguments.assets` deve ser array
- Cada asset deve ter `image` ou `video` com objeto contendo `url`

---

## 3. Formato do Payload MCP

### 3.1 Request

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "create_post",
    "arguments": {
      "organizationId": "org_xxx",
      "channelId": "channel_xxx",
      "text": "Conteúdo do post... [ID:1234]",
      "schedulingType": "automatic",
      "assets": [
        {
          "image": {
            "url": "https://raw.githubusercontent.com/.../Banner.png?t=1234567890"
          }
        },
        {
          "image": {
            "url": "https://raw.githubusercontent.com/.../Screenshot_11.jpg?t=1234567890"
          }
        }
      ]
    }
  },
  "id": 1
}
```

### 3.2 Response (SSE)

```json
data: {
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Post created successfully"
      }
    ],
    "isError": false
  }
}
```

---

## 4. Estratégia de Retry

| Tentativa | Delay | Jitter Máx | Acumulado |
|-----------|-------|------------|-----------|
| 1 | 5s | 0.5s | ~5.25s |
| 2 | 15s | 1.5s | ~20.75s |
| 3 | 30s | 3.0s | ~53.75s |

**Total máximo com retry + fallback entre 4 providers:** ~3 min 35s
**Tempo de recuperação (RNF002):** < 60s para um provider individual.

---

## 5. Rate Limiting

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| Max requests/min | 5 | Quota gratuita Gemini: ~10-15 req/min |
| Delay mínimo | 12s | Distribuir requests uniformemente |
| Janela de expurgo | 60s | Reset natural da quota |

---

## 6. Logs Estruturados

| Tag | Uso |
|----|-----|
| `[AI_PROVIDER]` | Início de tentativa com provider |
| `[SUCCESS]` | Provider retornou conteúdo |
| `[FALLBACK]` | Provider falhou, indo para próximo |
| `[RETRY]` | Retentativa com backoff |
| `[ERROR]` | Erro não recuperável |
| `[BUFFER]` | Operações com Buffer |
| `[MCP]` | Comunicação MCP |
| `[QUOTA]` | Rate limiting |

---

## 7. Dependências

```
google-genai >= 1.0.0    → SDK Google Gemini
requests >= 2.31.0       → REST APIs (Groq, OpenRouter, MCP)
python-dotenv >= 1.0.0   → Variáveis de ambiente
```
