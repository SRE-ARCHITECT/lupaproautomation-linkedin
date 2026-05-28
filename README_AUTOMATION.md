# 🚀 Lupa PRO - Automação de Marketing LinkedIn (v2.0)

Sistema autônomo de geração de conteúdo e agendamento de postagens utilizando Inteligência Artificial de ponta e infraestrutura do GitHub.

## 🧠 Arquitetura Técnica

### 1. Motor de Geração (AI Fallback System)
O sistema utiliza um gerenciador de providers com fallback automático e retry inteligente:

1. **Primário:** Gemini 2.5 Flash (Google)
2. **Secundário:** Gemini 2.0 Flash Lite (Google)
3. **Terceário:** Groq Llama 3 (Groq Cloud)
4. **Contingência:** OpenRouter (fallback universal)

### 2. Retry Inteligente
- Tentativas com backoff: 5s → 15s → 30s
- Detecção automática de erros recuperáveis (429, timeout, rate limit)
- Fallback automático entre providers

### 3. Rate Limiter Interno
- Máximo de 5 requests por minuto
- Delay mínimo de 12s entre chamadas
- Fila de processamento automática

### 4. Validação de Payload
Validação antes do envio ao MCP do Buffer:
- assets sempre como array
- Campos obrigatórios verificados
- URLs validadas

### 5. Inteligência Anti-Repetição
- **Histórico Persistente:** post_history.txt
- **Git Persistence:** Commit automático do histórico

### 6. Carrossel Inteligente
- Detecção dinâmica de assets
- Seleção aleatória de screenshots
- Cache-busting via timestamp

## 📂 Estrutura de Pastas

```
/.github/workflows/       → daily_post.yml (Agendamento)
/assets/                  → Screenshots e mídias
/services/                → Lógica de negócio
  ai_provider_manager.py  → Gerenciador de providers
  retry_handler.py        → Retry com backoff
  quota_manager.py        → Rate limiter interno
/providers/               → Providers de IA
  gemini.py               → Google Gemini
  groq.py                 → Groq Cloud
  openrouter.py           → OpenRouter
/utils/                   → Utilitários
  validate_buffer_payload.py → Validação de payload MCP
generate_and_post.py      → Entry point
post_history.txt          → Histórico de posts
requirements.txt          → Dependências
```

## ⚙️ Configuração de Secrets (GitHub)

| Secret | Obrigatório | Descrição |
|--------|-------------|-----------|
| `BUFFER_ACCESS_TOKEN` | Sim | Token da API do Buffer |
| `BUFFER_ORG_ID` | Sim | ID da organização no Buffer |
| `BUFFER_PROFILE_ID` | Sim | ID do perfil LinkedIn |
| `GEMINI_API_KEY` | Sim | Chave Google AI Studio |
| `GROQ_API_KEY` | Não* | Chave Groq Cloud |
| `OPENROUTER_API_KEY` | Não* | Chave OpenRouter |

*Necessário pelo menos um provider além do Gemini.

## 🔄 Execução Manual

1. Vá até a aba **Actions** no GitHub
2. Selecione **Daily LinkedIn Post**
3. Clique em **Run workflow**

---

## 📚 Documentação Técnica

| Documento | Descrição |
|-----------|-----------|
| [`docs/PRD.md`](docs/PRD.md) | Product Requirements Document |
| [`docs/BLUEPRINT.md`](docs/BLUEPRINT.md) | Blueprint técnico e arquitetura |
| [`docs/SKILL.md`](docs/SKILL.md) | Runbook operacional e troubleshooting |

---

**Desenvolvido para o ecossistema Lupa PRO.** 👁️🛡️🚀📈
