# 🚀 Lupa PRO - Automação de Marketing LinkedIn (v1.0)

Sistema autônomo de geração de conteúdo e agendamento de postagens utilizando Inteligência Artificial de ponta e infraestrutura do GitHub.

## 🧠 Arquitetura Técnica

O sistema foi desenhado para ser resiliente e autossuficiente através das seguintes camadas:

### 1. Motor de Geração (AI Fallback System)
O script `generate_and_post.py` utiliza um sistema de redundância tripla para garantir que o post diário seja gerado sem falhas:
1.  **Primário:** Gemini 2.0 Flash (Alta complexidade e raciocínio).
2.  **Secundário:** Gemini 1.5 Flash (Resiliência e alta cota).
3.  **Contingência Final:** Groq (Llama 3 70B) (Velocidade e disponibilidade).

### 2. Infraestrutura de Automação
- **GitHub Actions:** O "despertador" que roda o código diariamente via Cron.
- **Buffer API:** O motor de agendamento que publica no LinkedIn.
- **GitHub Raw API:** Hospeda as imagens de marketing dinamicamente para o Buffer.

## 📂 Estrutura de Pastas

- `/.github/workflows/`: Contém o arquivo `daily_post.yml` (Agendamento diário).
- `/assets/`: Onde residem as capturas de tela do carrossel.
- `generate_and_post.py`: O "cérebro" do sistema (Lógica de IA + Buffer).
- `requirements.txt`: Dependências Python.
- `.gitignore`: Garante que seus arquivos `.env` locais nunca vazem para a web.

## ⚙️ Configuração de Secrets (GitHub)

Para o sistema funcionar, o repositório deve ter os seguintes segredos configurados:
- `BUFFER_ACCESS_TOKEN`: Token de acesso da API do Buffer.
- `BUFFER_ORG_ID`: ID da sua organização no Buffer.
- `BUFFER_PROFILE_ID`: ID do perfil do LinkedIn.
- `GEMINI_API_KEY`: Chave de API do Google AI Studio.
- `GROQ_API_KEY`: Chave de API da Groq Cloud.

## 📸 Como adicionar novas imagens ao Carrossel

1.  Mova as novas imagens para a pasta `assets/`.
2.  Nomeie-as no padrão `Screenshot_X.jpg` ou atualize a lógica no arquivo `generate_and_post.py` (linha 105).
3.  Faça o `git commit` e `push`. O sistema passará a usar as novas fotos automaticamente.

## 🔄 Execução Manual

Para forçar um post agora mesmo sem esperar o horário agendado:
1.  Vá até a aba **Actions** no seu repositório GitHub.
2.  Selecione **Daily LinkedIn Post**.
3.  Clique em **Run workflow**.

---
**Desenvolvido por Cerebro para o ecossistema Lupa PRO.** 👁️🛡️🚀📈
