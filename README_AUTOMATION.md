# 🚀 Lupa PRO - Automação de Marketing LinkedIn (v1.1)

Sistema autônomo de geração de conteúdo e agendamento de postagens utilizando Inteligência Artificial de ponta e infraestrutura do GitHub.

## 🧠 Arquitetura Técnica

O sistema foi desenhado para ser resiliente e autossuficiente através das seguintes camadas:

### 1. Motor de Geração (AI Fallback System)
O script `generate_and_post.py` utiliza um sistema de redundância tripla para garantir que o post diário seja gerado sem falhas:
1.  **Primário:** Gemini 2.0 Flash (Alta complexidade e raciocínio).
2.  **Secundário:** Gemini 1.5 Flash (Resiliência e alta cota).
3.  **Contingência Final:** Groq (Llama 3 70B) (Velocidade e disponibilidade).

### 2. Inteligência Anti-Repetição
- **Histórico Persistente:** O sistema salva cada post gerado em `post_history.txt`.
- **Git Persistence:** O GitHub Actions faz o *commit* automático do histórico após cada execução, garantindo que a IA nunca repita o mesmo conteúdo nos dias seguintes.

### 3. Carrossel Inteligente
- **Detecção Dinâmica:** O sistema varre a pasta `/assets/` e seleciona aleatoriamente entre 3 a 5 capturas de tela para compor o carrossel do dia. 
- **Fallback Visual:** Caso não existam screenshots, utiliza o banner principal.

## 📂 Estrutura de Pastas

- `/.github/workflows/`: Contém o arquivo `daily_post.yml` (Agendamento diário).
- `/assets/`: Screenshots e mídias do projeto.
- `generate_and_post.py`: O "cérebro" do sistema (Lógica de IA + Buffer).
- `post_history.txt`: Log de conteúdos já postados (gerenciado automaticamente).
- `requirements.txt`: Dependências Python.

## ⚙️ Configuração de Secrets (GitHub)

Para o sistema funcionar, o repositório deve ter os seguintes segredos configurados em *Settings > Secrets and variables > Actions*:
- `BUFFER_ACCESS_TOKEN`: Token de acesso da API do Buffer.
- `BUFFER_ORG_ID`: ID da sua organização no Buffer.
- `BUFFER_PROFILE_ID`: ID do perfil do LinkedIn.
- `GEMINI_API_KEY`: Chave de API do Google AI Studio.
- `GROQ_API_KEY`: Chave de API da Groq Cloud.

## 📸 Adicionando Novas Imagens

Basta subir qualquer arquivo `.jpg` ou `.png` que contenha a palavra "Screenshot" no nome para a pasta `assets/`. O script irá detectá-lo e incluí-lo na rotatividade do carrossel automaticamente no próximo ciclo.

## 🔄 Execução Manual

Para forçar um post agora mesmo:
1.  Vá até a aba **Actions** no seu repositório GitHub.
2.  Selecione **Daily LinkedIn Post**.
3.  Clique em **Run workflow**.

---
**Desenvolvido para o ecossistema Lupa PRO.** 👁️🛡️🚀📈
