# PRD — Automação IA + Buffer para LinkedIn

## Versão

| Versão | Data | Autor | Descrição |
|--------|------|-------|-----------|
| 2.0 | 2026-05-28 | Lupa PRO Team | Correção de falhas e arquitetura modular |

---

## Objetivo

Corrigir completamente o fluxo de geração e agendamento automático de posts da automação atual, eliminando falhas de:

- Quota da API Gemini
- Fallback inválido de modelos
- Payload incorreto enviado ao MCP/Buffer
- Ausência de retry inteligente
- Falta de resiliência entre providers de IA

O sistema deve operar de forma estável, resiliente e automática via GitHub Actions.

---

## Problemas Resolvidos (v1.x → v2.0)

### 1. Gemini — Quota Exceeded (429)

**Sintoma:** `429 RESOURCE_EXHAUSTED` em `gemini-2.0-flash`

**Causa:** Modelo gratuito sem quota suficiente + sem retry.

**Solução:**
- Substituído por `gemini-2.5-flash` como primário
- `gemini-2.0-flash-lite` como fallback Google
- Retry com backoff 5s/15s/30s para erros 429
- Rate limiter interno: máx 5 req/min

### 2. Fallback Gemini 1.5 Inválido (404)

**Sintoma:** `404 NOT_FOUND: models/gemini-1.5-flash is not found`

**Causa:** Modelo descontinuado.

**Solução:** Removido `gemini-1.5-flash`. Substituído por `gemini-2.0-flash-lite`.

### 3. Payload MCP Incorreto

**Sintoma:** `Invalid input: expected array, received object at path: ["assets"]`

**Causa:** `assets` enviado como objeto `{"images": [...]}`.

**Solução:** `assets` agora é um array de objetos `{"image": {"url": "..."}}`.

### 4. Ausência de Retry

**Sintoma:** Falha instantânea em qualquer erro de rede/quota.

**Solução:** Retry inteligente com exponential backoff e detecção de erros recuperáveis.

### 5. Falta de Resiliência entre Providers

**Sintoma:** Apenas 2 providers (Gemini + Groq), sem fallback adicional.

**Solução:** 4 providers encadeados com fallback automático.

---

## Arquitetura do Sistema

```txt
generate_and_post.py (entry point)
  │
  ├── AIProviderManager
  │     ├── Gemini (gemini-2.5-flash → gemini-2.0-flash-lite)
  │     │     └── Retry: 5s → 15s → 30s
  │     ├── Groq (llama-3.3-70b-versatile)
  │     │     └── Retry: 5s → 15s → 30s
  │     ├── OpenRouter (meta-llama/llama-3.3-70b-instruct)
  │     │     └── Retry: 5s → 15s → 30s
  │     └── Static Fallback
  │
  ├── Carrossel Builder
  │     ├── Banner (fixo)
  │     ├── Brand Black (fixo)
  │     ├── Screenshots (2 aleatórias)
  │     └── Brand White (fixo)
  │
  ├── Validação de Payload
  │     └── validate_buffer_payload.py
  │
  └── MCP Buffer Client
        └── enviar_via_mcp()
```

---

## Fluxo de Execução

```txt
Generate Content
  │
  ▼
Validate Provider Quota
  │
  ▼
AIProviderManager.generate()
  │
  ├── GeminiProvider.generate()
  │     ├── Tentativa 1 → 5s se erro recuperável
  │     ├── Tentativa 2 → 15s se erro recuperável
  │     ├── Tentativa 3 → 30s se erro recuperável
  │     └── Falha → próximo provider
  │
  ├── GroqProvider.generate()
  │     ├── Retry 5s → 15s → 30s
  │     └── Falha → próximo provider
  │
  ├── OpenRouterProvider.generate()
  │     ├── Retry 5s → 15s → 30s
  │     └── Falha → static fallback
  │
  └── Static Fallback
        └── Texto genérico com timestamp único
  │
  ▼
Build Carousel URLs
  │
  ▼
Validate Payload (Zod-style)
  │
  ▼
Send to Buffer MCP
  │
  ▼
Commit History
```

---

## Requisitos Funcionais

| ID | Descrição | Status |
|----|-----------|--------|
| RF001 | Gerar posts usando IA com fallback automático | ✅ |
| RF002 | Fallback automático se Gemini falhar | ✅ |
| RF003 | Fluxo nunca deve interromper por erro de provider | ✅ |
| RF004 | Enviar múltiplas imagens corretamente no carrossel | ✅ |
| RF005 | Validar payload antes do envio ao MCP | ✅ |

## Requisitos Não Funcionais

| ID | Descrição | Status |
|----|-----------|--------|
| RNF001 | Sistema resiliente com fallback em 4 níveis | ✅ |
| RNF002 | Tempo máximo de recuperação: 60s | ✅ |
| RNF003 | Compatível com GitHub Actions | ✅ |
| RNF004 | Compatível com Python 3.10+ | ✅ |

---

## Estrutura do Projeto

```txt
/
├── .github/workflows/
│   └── daily_post.yml          → Agendamento diário (13:00 UTC)
├── assets/                      → Imagens do carrossel
├── docs/
│   ├── PRD.md                   → Este documento
│   ├── BLUEPRINT.md             → Blueprint técnico
│   └── SKILL.md                 → Runbook operacional
├── services/
│   ├── ai_provider_manager.py   → Orquestrador de providers
│   ├── retry_handler.py         → Retry com backoff
│   └── quota_manager.py         → Rate limiter
├── providers/
│   ├── gemini.py                → Google Gemini
│   ├── groq.py                  → Groq Cloud
│   └── openrouter.py            → OpenRouter
├── utils/
│   └── validate_buffer_payload.py → Validação de payload
├── generate_and_post.py         → Entry point
├── post_history.txt              → Histórico de posts
└── requirements.txt              → Dependências Python
```
