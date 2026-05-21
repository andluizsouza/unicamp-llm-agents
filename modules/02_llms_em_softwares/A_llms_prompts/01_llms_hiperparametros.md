# LLMs e Hiperparâmetros: Da Teoria à Engenharia de Sistemas

## TL;DR / Resumo Executivo
O objetivo central deste módulo é capacitar o desenvolvedor a transitar do papel de usuário casual de interfaces como o ChatGPT para o papel de **engenheiro de LLMs**, focado na integração desses modelos em sistemas reais via **API**. Para isso, é fundamental compreender as diferentes categorias de modelos, como escolher o provedor adequado e como controlar o comportamento da geração de texto através do ajuste técnico de **hiperparâmetros**.

## Conceitos Fundamentais
*   **LLMs (Large Language Models):** Modelos de linguagem baseados na arquitetura **Transformers**, treinados em volumes massivos de dados (trilhões de tokens) para prever o próximo token em uma sequência.
*   **Mecanismo de Atenção:** Componente dos Transformers que permite ao modelo capturar relações semânticas complexas entre palavras (tokens) em um contexto.
*   **Tokens:** Unidades básicas de processamento de texto; podem ser palavras ou partes delas.
*   **RLHF (Reinforcement Learning from Human Feedback):** Técnica de aprendizado por reforço com intervenção humana usada para alinhar o comportamento do modelo com instruções específicas.
*   **Hiperparâmetros:** Parâmetros externos definidos pelo desenvolvedor que não alteram o conhecimento do modelo, mas ajustam **como** ele escolhe as palavras na saída (ex: criatividade vs. determinismo).
*   **Janela de Contexto (Context Window):** O limite total de tokens (entrada + saída) que um modelo consegue processar de uma só vez.

## Matrizes de Comparação

### 1. Tamanho do Modelo

| Categoria | Definição | Quando Usar / Exemplos | Pontos Positivos | Pontos Negativos |
| :--- | :--- | :--- | :--- | :--- |
| **Modelos Pequenos (1B-13B)** | Modelos com menor número de parâmetros. | Tarefas simples, dispositivos móveis, fine-tuning específico (ex: Llama 3.1 8B). | Baixo custo, baixa latência, podem ser rodados localmente. | Limitação em seguir instruções complexas ou raciocínio avançado. |
| **Modelos Grandes (100B+)** | Modelos massivos com alta capacidade computacional. | Raciocínio complexo, tarefas multimodais (ex: GPT-4o, Claude 3.5). | Desempenho superior em quase todas as tarefas complexas. | Altíssimo custo operacional e maior latência. |

### 2. Propriedade do Modelo

| Categoria | Definição | Quando Usar / Exemplos | Pontos Positivos | Pontos Negativos |
| :--- | :--- | :--- | :--- | :--- |
| **Open-Source** | Modelos com pesos disponíveis para download e hospedagem própria. | Quando a privacidade é crítica ou para evitar taxas por token (ex: Mistral, Llama). | Maior controle, sem custo por token, privacidade de dados. | Exige infraestrutura própria (GPUs) e gerenciamento de segurança. |
| **Proprietários** | Modelos fechados acessados exclusivamente via API paga. | Desenvolvimento rápido de produtos SaaS sem gerência de hardware (ex: GPT, Gemini). | Facilidade de uso (API), escalabilidade imediata, sem gerência de hardware. | Custo por token, menos controle sobre os dados e sobre os pesos do modelo. |

### 3. Tipo de Treinamento

| Categoria | Definição | Quando Usar / Exemplos | Pontos Positivos | Pontos Negativos |
| :--- | :--- | :--- | :--- | :--- |
| **Base Models** | Modelos que apenas completam texto estatisticamente. | Preenchimento de texto ou quando se deseja treinar do zero. | Úteis para tarefas de preenchimento bruto. | Não seguem comandos diretamente; exigem prompts complexos. |
| **Instruction-tuned** | Modelos treinados para agir como assistentes e seguir ordens. | Chatbots, assistentes técnicos, ferramentas de produtividade. | Entendem diálogos e comandos de forma natural. | Podem ter comportamentos enviesados pelo treinamento de alinhamento. |

## Diagrama de Fluxo Lógico

Abaixo, o passo a passo de como um sistema processa uma requisição para uma LLM, desde a entrada até a aplicação dos hiperparâmetros na saída:

1.  **Entrada (Prompt):** O usuário ou sistema envia um texto de entrada via API.
2.  **Tokenização:** O texto é quebrado em tokens (unidades numéricas que o modelo entende).
3.  **Processamento (Camadas Transformer):** O modelo utiliza o mecanismo de atenção para entender o contexto e as relações entre os tokens.
4.  **Distribuição de Probabilidades:** O modelo gera uma lista de possíveis próximos tokens, cada um com uma probabilidade de ocorrência.
5.  **Aplicação de Hiperparâmetros:**
    *   **Temperature:** Ajusta a aleatoriedade. Se próxima de 0, escolhe o mais provável (determinístico); se alta (>1), diversifica as escolhas (criativo).
    *   **Top-K / Top-P:** Filtram a lista de candidatos. O **Top-K** limita aos $K$ tokens mais prováveis; o **Top-P** seleciona o menor conjunto cujo acumulado de probabilidade atinja o valor $P$.
6.  **Seleção do Token:** Um token é escolhido com base nos filtros acima.
7.  **Loop de Geração:** O processo se repete (o token gerado volta para a entrada) até que o modelo atinja o **Max Tokens** definido ou uma sequência de parada (**Stop Sequence**).
8.  **Saída Final:** O texto completo é retornado ao sistema.