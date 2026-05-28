# Skill — Runbook Operacional da Automação LinkedIn Lupa PRO

---

## 1. Visão Geral

Automação diária de postagem no LinkedIn utilizando IA generativa com fallback multi-provider e agendamento via Buffer MCP.

**Stack:** Python 3.10+, GitHub Actions, Google Gemini, Groq, OpenRouter, Buffer MCP

---

## 2. Setup Inicial

### 2.1 Secrets do GitHub

Configurar em **Settings > Secrets and variables > Actions**:

| Secret | Obrigatório | Como obter |
|--------|-------------|------------|
| `BUFFER_ACCESS_TOKEN` | ✅ | Buffer Admin > API > Generate Token |
| `BUFFER_ORG_ID` | ✅ | Buffer Admin > Organization Settings |
| `BUFFER_PROFILE_ID` | ✅ | Buffer Admin > Profile > URL (último segmento) |
| `GEMINI_API_KEY` | ✅ | [aistudio.google.com](https://aistudio.google.com) > API Keys |
| `GROQ_API_KEY` | ❌* | [console.groq.com](https://console.groq.com) > Keys |
| `OPENROUTER_API_KEY` | ❌* | [openrouter.ai](https://openrouter.ai) > Keys |

*\*Necessário pelo menos um provider além do Gemini.*

### 2.2 Assets

Adicionar imagens em `/assets/`:
- `Banner.png` — Slide de abertura (obrigatório)
- `Screenshot_11.jpg` — Brand black (obrigatório)
- `Screenshot_.jpg` — Brand white/CTA (obrigatório)
- `Screenshot_N.jpg` — Screenshots para sorteio (opcional, N = 0-9)

---

## 3. Operação

### 3.1 Agendamento Automático

O workflow roda diariamente às **13:00 UTC** (10:00 BRT):
```yaml
schedule:
  - cron: '0 13 * * *'
```

### 3.2 Execução Manual

1. Acessar **Actions** > **Daily LinkedIn Post**
2. Clicar **Run workflow** > **Run workflow**
3. Acompanhar logs em tempo real

### 3.3 Dry Run (Teste Local)

```bash
# Sem BUFFER_ACCESS_TOKEN = modo simulação
python generate_and_post.py
```

---

## 4. Fluxo de Execução Detalhado

### 4.1 Geração de Conteúdo

```txt
1. build_prompt()
   ├── Lê post_history.txt (últimos 2000 chars)
   ├── Sorteia ângulo criativo (7 opções)
   └── Monta prompt completo

2. AIProviderManager.generate()
   ├── Gemini 2.5 Flash → retry 5s/15s/30s
   │   └── Gemini 2.0 Flash Lite → retry 5s/15s/30s
   ├── Groq Llama 3 → retry 5s/15s/30s
   ├── OpenRouter Llama 3 → retry 5s/15s/30s
   └── Static Fallback (sempre funciona)
```

### 4.2 Montagem do Carrossel

```txt
1. Banner.png (abertura)
2. Screenshot_11.jpg (brand black)
3-4. 2 screenshots aleatórias (prova social)
5. Screenshot_.jpg (CTA/brand white)
```

Máximo de 6 imagens. Cache-busting via `?t={timestamp}`.

### 4.3 Envio ao Buffer

```txt
1. Valida payload (validate_create_post_payload)
2. POST para https://mcp.buffer.com/mcp
3. Lê resposta SSE (data: {...})
4. Verifica erro no resultado
5. Retorna sucesso/falha
```

---

## 5. Tratamento de Erros

### 5.1 Erros Recuperáveis (retry automático)

| Erro | Ação |
|------|------|
| `429 RESOURCE_EXHAUSTED` | Retry 5s → 15s → 30s |
| `timeout` | Retry 5s → 15s → 30s |
| `rate limit` | Retry 5s → 15s → 30s |
| `connection error` | Retry 5s → 15s → 30s |
| `500/502/503` | Retry 5s → 15s → 30s |

### 5.2 Erros Não Recuperáveis (fallback imediato)

| Erro | Ação |
|------|------|
| `400 INVALID_ARGUMENT` | Próximo provider |
| `404 model not found` | Próximo provider |
| `API key not valid` | Próximo provider |
| `Invalid input` (payload) | Falha, loga erro |

### 5.3 MCP Errors

| Erro | Causa | Ação |
|------|-------|------|
| `expected array, received object` | `assets` como objeto | Corrigir payload |
| `unrecognized_keys: url` | Asset sem `image`/`video` wrapper | Envolver em `{"image": {"url": ...}}` |
| `-32602` validation error | Payload malformado | Validar antes de enviar |

---

## 6. Manutenção

### 6.1 Adicionar Novas Imagens

```bash
# 1. Colocar imagem em assets/
# 2. Nome deve conter "Screenshot" para detecção automática
# 3. Formatos aceitos: .jpg, .jpeg, .png
# 4. Commit e push
git add assets/nova_imagem.jpg
git commit -m "feat: adiciona nova screenshot ao carrossel"
git push
```

### 6.2 Verificar Histórico

```bash
cat post_history.txt | tail -20
```

### 6.3 Testar Provider Individual

```python
python -c "
from providers.gemini import GeminiProvider
p = GeminiProvider('SUA_KEY')
result = p.generate('teste prompt')
print(result)
"
```

---

## 7. Troubleshooting

### 7.1 Post Não Aparece no LinkedIn

1. Verificar **Buffer Queue** → pending posts
2. Verificar **Status Code MCP** → 200 = sucesso
3. Verificar `post_history.txt` → conteúdo foi gerado?

### 7.2 Todos os Providers Falham

1. Verificar secrets válidos
2. Verificar quota do Gemini
3. Verificar conectividade de rede
4. Static fallback sempre funciona (texto genérico)

### 7.3 Erro de Payload

```bash
python -c "
from utils.validate_buffer_payload import validate_create_post_payload
# Testar payload atual
"
```

### 7.4 Workflow Não Roda no Horário

1. Verificar **Actions** > **Daily LinkedIn Post** > enabled?
2. Verificar cron: `0 13 * * *` = 13:00 UTC
3. Disparar manualmente para testar

---

## 8. Arquivos de Log

Não há arquivos de log persistentes. Todo log é stdout do GitHub Actions.

Para debug local:
```bash
python generate_and_post.py 2>&1 | tee run_log.txt
```

---

## 9. Rollback

Se necessário reverter para versão anterior:

```bash
git revert HEAD
git push origin main
```

Ou reverter para commit específico:
```bash
git revert <commit-hash>
git push origin main
```
