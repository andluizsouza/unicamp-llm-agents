# Avaliação de Sistemas com Large Language Models (LLMs)

## TL;DR / Resumo Executivo
O objetivo central deste bloco é compreender que a avaliação de LLMs não é universal, mas **dependente do contexto** (ex: precisão no ramo jurídico vs. naturalidade em chatbots). Avaliar sistemas de IA envolve equilibrar a qualidade das respostas (fidelidade, clareza, factualidade) com métricas de engenharia como **custo, latência (P95) e throughput**, permitindo decisões fundamentadas entre o uso de APIs proprietárias ou modelos locais quantizados.

## Conceitos Fundamentais
*   **LLM-as-a-Judge (LLM Juiz):** Técnica onde um modelo de linguagem mais capaz (ex: GPT-4o) analisa e pontua as respostas produzidas por outro modelo.
*   **Latência P95:** Métrica de performance que indica o tempo máximo em que 95% das requisições foram processadas, sendo essencial para medir a experiência do usuário.
*   **Escala Likert:** Escala de pontuação (geralmente de 1 a 5) utilizada por avaliadores humanos ou LLMs para julgar critérios como clareza e utilidade.
*   **Quantização:** Processo de reduzir a precisão dos pesos de um modelo (ex: de 32 bits para 4 bits) para diminuir o consumo de memória (VRAM) e permitir a execução em hardware local.
*   **Métricas Textuais Clássicas:** Algoritmos (BLEU, ROUGE) que comparam a sobreposição de palavras entre uma resposta gerada e uma referência "padrão ouro".
*   **Similaridade Semântica (BERTScore):** Avaliação baseada em modelos de linguagem (como BERT) que identifica se duas frases têm o mesmo significado, mesmo usando palavras diferentes.

## Matriz de Comparação

### 1. O que é importante na avaliação de modelo LLM?

| Domínio / Aplicação | Foco Principal | Critérios / Detalhes |
| :--- | :--- | :--- |
| **Chatbot** | Naturalidade | Evitar respostas robóticas para que a conversa pareça humana. |
| **Ramo Jurídico** | Precisão | Proibição de inventar leis ou alíneas. |
| **Saúde** | Confiabilidade | Alta confiabilidade para evitar a invenção de doenças. |
| **Código** | Funcionalidade | O código gerado deve compilar; erros mínimos de sintaxe, como um ponto e vírgula, são críticos. |
| **RAG** | Fidelidade | Estrita aderência e fidelidade ao contexto fornecido. |
| **Atendimento** | Custo e Latência | Foco no equilíbrio entre o valor por token e a rapidez da resposta. |

### 2. Metodologias de Avaliação de Qualidade

| Metodologia | Definição | Quando Usar | Pontos Positivos | Pontos Negativos |
| :--- | :--- | :--- | :--- | :--- |
| **Humana** | Especialistas revisam e pontuam as respostas. | Casos críticos (saúde/jurídico) e validação final. | Alta validade e percepção de nuances humanas. | Cara, lenta, não escalável e sujeita a fadiga. |
| **Métricas Textuais (BLEU/ROUGE)** | Comparação matemática de palavras exatas. | Tradução (BLEU) e sumarização (ROUGE). | Rápidas, baratas e objetivas. | Ignoram semântica e sinônimos; penalizam criatividade. |
| **LLM-as-a-Judge** | Um LLM atua como juiz imparcial. | Avaliação em larga escala e pipelines de automação. | Escalável, consistente e rápida. | Pode ter vieses (prefere respostas longas) e instabilidade. |

---

#### 2.1 Limitações do LLM-as-a-Judge

O conceito de **LLM-as-a-Judge** (ou LLM como juiz) consiste em utilizar um modelo de linguagem mais capaz para analisar e pontuar as respostas produzidas por outro modelo, avaliando critérios como factualidade, clareza e completude. Embora seja uma solução para a baixa escalabilidade da avaliação humana, essa abordagem apresenta limitações técnicas e vieses importantes que devem ser considerados.

#### 2.1.1 Vieses de Avaliação (Biases)
Os modelos de linguagem apresentam comportamentos sistemáticos que podem distorcer a nota atribuída:
*   **Viés de Verbocidade (Response Bias):** O LLM juiz tende a preferir respostas mais longas e detalhadas, atribuindo notas mais altas para textos mais "verbosos", mesmo que a factualidade seja a mesma de uma resposta curta.
*   **Self-enhancement (Autopreferência):** Modelos tendem a preferir saídas geradas por eles mesmos ou por modelos da mesma família (ex: o GPT-4 prefere respostas do próprio GPT-4). Por isso, a "regra de ouro" é nunca usar o mesmo modelo como juiz e avaliado ao mesmo tempo.
*   **Viés de Ordem:** Em avaliações comparativas (A vs B), os modelos demonstram sensibilidade à ordem de apresentação, muitas vezes preferindo a primeira opção apresentada no prompt.

#### 2.1.2 Instabilidade e Sensibilidade
A confiabilidade do LLM como juiz pode ser afetada por fatores de configuração:
*   **Sensibilidade ao Prompt:** Pequenas mudanças de palavras no final das instruções de avaliação podem alterar drasticamente o resultado final.
*   **Temperatura:** Temperaturas maiores que zero introduzem aleatoriedade, gerando notas diferentes para a mesma entrada em execuções distintas. A recomendação técnica é utilizar **temperatura zero** para garantir determinismo.

#### 2.1.3 Problemas de Correlação e Validade
A eficácia do juiz automatizado é geralmente medida pela correlação com avaliadores humanos (variando entre 0.7 e 0.85), mas isso traz desafios:
*   **Qualidade do Humano:** Uma correlação alta com humanos não garante que o LLM seja um bom juiz se os avaliadores humanos originais forem ruins ou estiverem fadigados. O LLM apenas mimetiza o comportamento humano, não necessariamente a "verdade" absoluta.
*   **Habilidade de Julgamento:** Se o prompt de avaliação não for extremamente específico sobre o que define um critério (como "factualidade"), o modelo pode alucinar ou atribuir notas arbitrárias.

#### 2.1.4 Mitigações Necessárias
Para reduzir o impacto dessas limitações, as fontes sugerem:
*   **Múltiplas Execuções:** Rodar a avaliação várias vezes e tirar uma média para estabilizar os resultados.
*   **Justificativas:** Pedir para o LLM juiz explicar o porquê de cada nota, o que ajuda na auditabilidade do processo.
*   **Amostragem Humana:** Validar uma pequena amostra (ex: 0,1%) manualmente para verificar se o juiz automatizado continua alinhado com os objetivos do sistema.

---

#### 2.2 Métricas Textuais

As métricas textuais clássicas são ferramentas de avaliação quantitativa automática que surgiram bem antes dos Large Language Models (LLMs),. Elas funcionam comparando a resposta gerada pelo modelo com uma resposta de referência, também chamada de **"Gold Standard"** ou padrão ouro.

#### 2.2.1 BLEU (Bilingual Evaluation Understudy)
O **BLEU** é uma métrica amplamente utilizada no campo da **tradução automática**. 

*   **Funcionamento:** Ele compara sequências de palavras (n-grams) entre o texto gerado e o texto de referência. Se a sequência de palavras for exatamente igual à referência, o valor da métrica é 1.
*   **Limitações:** O BLEU é limitado por não considerar a semântica ou sinônimos,. Para o algoritmo, palavras como "gato" e "felino" são tratadas como termos totalmente diferentes, o que pode resultar em uma pontuação baixa mesmo que o significado da frase seja idêntico ao da referência.
*   **Implementação:** Em Python, é comum utilizar a biblioteca **NLTK** para calcular o `sentence_bleu`.

#### 2.2.2 ROUGE (Recall-Oriented Understudy for Gisting Evaluation)
O **ROUGE** é uma métrica que possui um foco maior em tarefas de **sumarização de texto**,.

*   **Funcionamento:** Ao contrário do BLEU, o ROUGE mede o quanto da referência está presente no texto gerado pelo modelo. Ele avalia a sobreposição de sequências de palavras entre os textos.
*   **Variações:** Existem diferentes tipos, como o **ROUGE-1** (focado em palavras individuais), **ROUGE-2** (focado em pares de palavras) e o **ROUGE-L** (focado na maior sequência comum). 
*   **Limitações:** Assim como o BLEU, o ROUGE penaliza o modelo caso ele não utilize a sequência exata de palavras da referência. Se o modelo trocar "respondeu corretamente" por "acertou a resposta", a métrica diminuirá por não encontrar o par exato de palavras.
*   **Implementação:** Pode ser implementado utilizando a biblioteca `rouge_score` em Python.

#### 2.2.3 BERTScore
Diferente das métricas clássicas que se baseiam apenas na escrita exata das palavras, o **BERTScore** foca na **similaridade semântica**,.

*   **Funcionamento:** Ele utiliza o modelo de linguagem **BERT** para comparar tokens individualmente. O processo envolve transformar as frases em vetores numéricos (embeddings) e calcular o **cosseno de similaridade** entre eles,.
*   **Vantagens:** Por utilizar o BERT, esta métrica consegue identificar que palavras escritas de formas diferentes possuem significados iguais ou parecidos (como "gato" e "felino"). Isso torna a avaliação muito mais robusta para entender a intenção e a correção semântica da resposta.
*   **Implementação:** Utiliza-se bibliotecas como `sentence_transformers` para codificar as frases e realizar a comparação vetorial.

#### 2.2.4 Matriz Comparativa de Métricas Automatizadas

| Métrica | Aplicação Principal | Base de Comparação | Considera Semântica? |
| :--- | :--- | :--- | :--- |
| **BLEU** | Tradução Automática | Sobreposição de n-grams (texto exato) | Não |
| **ROUGE** | Sumarização | Cobertura da referência no texto gerado | Não |
| **BERTScore** | Similaridade Semântica | Comparação de vetores (embeddings), | Sim |

**Nota Final:** Embora o BLEU e o ROUGE ainda sejam usados, eles são considerados limitados por natureza. Em sistemas modernos de software baseados em LLM, recomenda-se preferir métricas mais profundas como o **BERTScore** ou o uso de **LLM-as-a-Judge** para avaliações mais próximas do julgamento humano.

---

### 3. Infraestrutura: API vs. Modelo Local

| Categoria | Quando Usar | Exemplos | Pontos Positivos | Pontos Negativos |
| :--- | :--- | :--- | :--- | :--- |
| **API Proprietária** | Prototipagem rápida e baixo volume de requisições. | GPT-4o, Gemini, Claude. | Facilidade de uso e escalabilidade imediata. | Custo por token e menor privacidade de dados sensíveis. |
| **Modelo Local** | Volume massivo (>1M req/mês) ou dados ultra sensíveis. | Llama 3.1, Mistral (via Olhama). | Privacidade total e sem custo variável por token. | Exige hardware caro (GPUs) e manutenção técnica. |

## Diagrama de Fluxo Lógico (Pipeline de Avaliação)

O processo para avaliar e escolher o melhor sistema de LLM segue este fluxo linear e iterativo:

1.  **Definição da Tarefa:** Identificar o foco principal (ex: precisão jurídica vs. naturalidade de chat).
2.  **Criação do Dataset de Teste:** Selecionar de 50 a 100 exemplos representativos, incluindo casos de borda (*edge cases*) para maior robustez.
3.  **Execução do Modelo:** Gerar as respostas para o subconjunto de testes utilizando os modelos candidatos.
4.  **Coleta de Métricas Técnicas:** Medir o custo estimado por token e a latência P95 das requisições.
5.  **Aplicação da Avaliação de Qualidade:**
    *   Usar **Métricas Textuais** para triagem rápida.
    *   Usar **LLM-as-a-Judge** (com temperatura 0 e justificativa) para escala.
    *   Usar **Avaliação Humana** em uma amostra (0,1%) para validar o juiz automatizado.
6.  **Análise de Correlação:** Verificar via Coeficiente de Kappa se as notas do LLM Juiz são parecidas com as dos humanos.
7.  **Decisão Final e Iteração:** Selecionar o modelo com melhor custo-benefício e refinar os prompts conforme os erros encontrados.