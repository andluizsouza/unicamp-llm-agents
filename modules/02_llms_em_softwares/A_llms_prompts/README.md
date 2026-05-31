# Bloco A: LLMs e Engenharia de Prompts

## TL;DR / Resumo Executivo
O Bloco A marca a transição do desenvolvedor de usuário casual para **engenheiro de sistemas baseados em LLMs**. Seu objetivo central é capacitar o aluno a integrar modelos de linguagem em aplicações reais via API, dominando desde a escolha e configuração de **hiperparâmetros** de geração até técnicas avançadas de **Engenharia de Prompt** — incluindo estratégias de Zero-shot, Few-shot, Chain-of-Thought e arquiteturas de **orquestração de inferência** (Self-Consistency e Self-Refinement) — para garantir saídas consistentes, previsíveis e prontas para consumo por sistemas de software.

## Conceitos Fundamentais (Tópicos Abordados)

- **Categorias de LLMs e Provedores**: Diferenciação entre modelos pequenos vs. grandes, open-source vs. proprietários e base models vs. instruction-tuned, com critérios de escolha para cada cenário.
- **Hiperparâmetros de Geração**: Controle do comportamento da saída via Temperature, Top-K, Top-P, Max Tokens e Stop Sequences — ajustando criatividade vs. determinismo sem alterar os pesos do modelo.
- **Engenharia de Prompt Estruturado**: Design disciplinado e iterativo de instruções com definição de persona, tarefa, contexto, formato de saída e restrições para integração em sistemas.
- **Injeção de Conteúdo e Janela de Contexto**: Técnicas para inserir dados externos (bancos de dados, documentos) no prompt e gestão dos limites de tokens, incluindo o fenômeno *Lost in the Middle*.
- **Estratégias de Ativação de Conhecimento**: Zero-shot (instrução direta), Few-shot (exemplos no contexto) e Chain-of-Thought (raciocínio passo a passo) como ferramentas progressivas de controle de qualidade.
- **Orquestração de Inferência**: Superação da natureza probabilística via Self-Consistency (votação por maioria entre N respostas) e Self-Refinement (loop de geração → crítica → refinamento).
- **Role Prompting**: Atribuição de papéis especializados no system prompt para condicionar domínio, tom e audiência da resposta.


## **Matriz de Conteúdo**: Aulas do Bloco A

| Aula | Tema Principal | Descrição Curta | Objetivo | Arquivo de Referência |
|------|----------------|----------------|----------|--------|
| 01 | LLMs e Hiperparâmetros | Categorias de modelos, provedores e controle de geração via Temperature, Top-K/P e Max Tokens | Capacitar o desenvolvedor a escolher e configurar LLMs para integração em sistemas via API. | [01_llms_hiperparametros.md](/modules/02_llms_em_softwares/A_llms_prompts/01_llms_hiperparametros.md) |
| 02 | Introdução à Engenharia de Prompt | Prompts estruturados, injeção de contexto, formato de saída e ciclo de refinamento | Transformar o desenvolvedor em projetista de sistemas com prompts previsíveis e interoperáveis. | [02_intro_prompts.md](/modules/02_llms_em_softwares/A_llms_prompts/02_intro_prompts.md) |
| 03 | Tipos de Prompts | Zero-shot, Few-shot, Chain-of-Thought e fluxo de decisão de engenharia | Apresentar estratégias progressivas para mitigar ambiguidade e variância nas respostas. | [03_tipos_prompts.md](/modules/02_llms_em_softwares/A_llms_prompts/03_tipos_prompts.md) |
| 04 | Prompts Avançados | Self-Consistency, Self-Refinement, Role Prompting e orquestração de inferência | Superar limitações probabilísticas com arquiteturas de controle e múltiplas chamadas coordenadas. | [04_prompts_avancados.md](/modules/02_llms_em_softwares/A_llms_prompts/04_prompts_avancados.md) |
| Prática | LLMs via API | Configuração e chamadas de modelos via API com ajuste de hiperparâmetros | Aplicar a integração de LLMs em código, explorando parâmetros de geração na prática. | [hands_on_llms_api.ipynb](/modules/02_llms_em_softwares/A_llms_prompts/hands_on_llms_api.ipynb) |
| Prática | Engenharia de Prompts | Implementação de técnicas de Zero-shot, Few-shot, CoT e orquestração | Aplicar as estratégias de prompting em cenários reais de desenvolvimento de software. | [hands_on_prompts.ipynb](/modules/02_llms_em_softwares/A_llms_prompts/hands_on_prompts.ipynb) |
