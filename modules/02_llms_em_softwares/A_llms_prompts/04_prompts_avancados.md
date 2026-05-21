# Orquestração de Inferência e Prompts Avançados

## TL;DR / Resumo Executivo
O objetivo central deste bloco é superar as limitações da natureza probabilística das LLMs (que podem cometer erros mesmo em prompts bem escritos) através da **orquestração de inferência**. Em vez de confiar em uma única resposta ($N=1$), o desenvolvedor utiliza fluxos de prompts e arquiteturas de controle para explorar a variância do modelo a favor da precisão, utilizando o próprio sistema como validador ou crítico para garantir resultados consistentes em tarefas complexas.

## Conceitos Fundamentais
*   **Orquestração de Inferência:** Mudança de paradigma de um "prompt único" para um fluxo de múltiplos prompts coordenados para aumentar a confiabilidade.
*   **Natureza Probabilística:** Característica técnica que faz com que modelos de linguagem possam alucinar ou errar fatos simples (como cálculos matemáticos) dependendo da probabilidade estatística de seus tokens de treinamento.
*   **LLM-as-a-Judge (Self-Refinement):** Uso de uma LLM para avaliar, criticar e fornecer feedback sobre a qualidade da própria saída ou da saída de outro modelo.
*   **Votação por Maioria (Self-Consistency):** Processo de gerar múltiplas respostas independentes e selecionar a mais frequente como a resposta final.
*   **Trade-off Custo-Qualidade:** Equilíbrio necessário entre o aumento da precisão (via múltiplas chamadas de API) e o aumento proporcional de latência e custo financeiro.

## Matriz de Comparação

| Técnica | Definição | Exemplos | Quando Usar | Pontos Positivos | Pontos Negativos |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Self-consistency** | Gera $N$ caminhos de raciocínio independentes e seleciona a resposta mais frequente. | Cálculos matemáticos, diagnósticos médicos e extração de dados críticos. | Tarefas com resposta objetiva (certo/errado claro) e baixa tolerância a erros. | Aumenta drasticamente a precisão em tarefas lógicas (ex: +17,9% em matemática). | Alto custo e alta latência (proporcional ao número $N$ de execuções). |
| **Self-refinement** | Loop iterativo onde o modelo gera, critica e refina sua própria resposta com base em critérios. | Geração de relatórios, revisão de código e escrita criativa de e-mails. | Quando a qualidade subjetiva (clareza, tom, naturalidade) é o critério principal. | Melhora a legibilidade (+13%) e fluência do texto (+14%) através de feedback iterativo. | Chamadas sequenciais aumentam a latência; modelos pequenos podem ter autocrítica fraca. |
| **Role Prompting** | Atribuição de papéis de especialistas no *system prompt* para condicionar o domínio do conhecimento. | "Você é um médico cardiologista" vs. "Você é um jornalista de saúde". | Qualquer tarefa que exija uma audiência específica ou domínio técnico delimitado. | Técnica de menor custo (chamada única) que otimiza tarefas de domínio específico. | Papéis inadequados podem introduzir distorções sistemáticas e vieses nos resultados. |

## Diagrama de Fluxo Lógico (Decisão de Engenharia)

Para selecionar a técnica de prompting avançado ideal, deve-se seguir este fluxo de decisão baseado nas características da tarefa:

1.  **A tarefa possui uma resposta objetiva e clara (Ex: matemática ou lógica)?**
    *   **SIM:** Implemente **Self-Consistency**. Execute a tarefa $N$ vezes (5 a 20 execuções), extraia apenas a conclusão final e aplique a votação por maioria (moda).
    *   **NÃO:** Prossiga para o próximo passo.
2.  **A resposta precisa ser melhorada iterativamente para atingir qualidade subjetiva?**
    *   **SIM:** Implemente **Self-Refinement**. Gere a V1 -> Realize a crítica com base em critérios (clareza/completude) -> Refine para V2 (até o critério de parada).
    *   **NÃO:** Prossiga para o próximo passo.
3.  **A tarefa exige apenas um tom ou domínio específico de conhecimento?**
    *   **SIM:** O **Role Prompting** é suficiente. Defina a persona ultra especialista no *system prompt* para alinhar a saída à audiência desejada.
4.  **Finalização:** Trate o prompt não apenas como texto, mas como uma **arquitetura de controle** integrada ao sistema.