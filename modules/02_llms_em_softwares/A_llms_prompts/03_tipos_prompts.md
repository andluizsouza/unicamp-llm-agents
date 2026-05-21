# Tipos de Prompts: Estratégias de Ativação de Conhecimento

## TL;DR / Resumo Executivo
O objetivo central deste bloco é apresentar estratégias para mitigar a **ambiguidade** e a **variância** nas respostas das LLMs, problemas causados por prompts subespecificados. Através das técnicas de **Zero-shot, Few-shot e Chain-of-Thought**, o desenvolvedor aprende a restringir o espaço de busca do modelo, garantindo saídas mais precisas, consistentes e auditáveis para integração em sistemas de software.

## Conceitos Fundamentais
*   **Zero-shot:** Técnica de instrução direta onde o modelo realiza uma tarefa baseando-se apenas no seu conhecimento prévio, sem exemplos adicionais no prompt.
*   **Few-shot:** Estratégia que fornece pares de entrada e saída (exemplos) para que o modelo aprenda o padrão esperado dentro do contexto da requisição.
*   **In-context Learning:** Aprendizado que ocorre dinamicamente durante a execução da consulta, onde o modelo infere formatos e critérios a partir dos exemplos fornecidos.
*   **Chain-of-Thought (CoT):** Técnica que instrui o modelo a gerar etapas intermediárias de raciocínio antes de apresentar a resposta final, sendo ideal para problemas lógicos ou matemáticos.
*   **Viés de Recência:** Tendência do modelo em dar maior peso ou repetir o padrão do último exemplo fornecido em um prompt de Few-shot.

## Matriz de Comparação

| Categoria | Definição | Exemplos | Quando Usar | Pontos Positivos | Pontos Negativos |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Zero-shot** | Instrução direta sem exemplos prévios. | "Classifique este ticket: [texto]". | Tarefas simples, senso comum e alto volume. | Baixo custo, baixa latência e fácil manutenção. | Alta ambiguidade e formato de saída imprevisível. |
| **Few-shot** | Fornecimento de 3 a 5 pares de entrada/saída. | "Ex 1: [A] -> [B]. Ex 2: [C] -> [D]. Agora faça: [E]". | Formatos específicos, classificações customizadas e consistência crítica. | Maior precisão, controle de formato e redução de alucinações. | Explosão de tokens (custo) e necessidade de curadoria de exemplos. |
| **Chain-of-Thought** | Indução de raciocínio passo a passo. | "Pense passo a passo antes de responder". | Cálculos, lógica, diagnósticos e múltiplos critérios. | Erros rastreáveis (auditabilidade) e melhor desempenho em tarefas complexas. | Alta latência e maior custo devido ao volume de tokens de saída. |

## Diagrama de Fluxo Lógico (Decisão de Engenharia)

Para otimizar o desenvolvimento e o custo de sistemas baseados em LLMs, recomenda-se seguir o seguinte fluxo de decisão:

1.  **Início (Zero-shot):** Comece sempre com um prompt simples para testar a capacidade base do modelo na tarefa.
2.  **Avaliação de Formato:** 
    *   A resposta está correta, mas o formato é inconsistente ou imprevisível?
    *   **Ação:** Implemente **Few-shot**, adicionando exemplos claros de entrada e saída esperada.
3.  **Avaliação de Raciocínio:**
    *   O formato está correto, mas o modelo comete erros de lógica ou cálculos?
    *   **Ação:** Utilize **Chain-of-Thought (CoT)** para forçar a decomposição do problema em etapas.
4.  **Refinamento Final (Combinados):**
    *   A tarefa é complexa e exige um formato rigoroso?
    *   **Ação:** Combine **Few-shot + CoT** para obter o máximo de precisão e controle estrutural.
5.  **Monitoramento de Produção:** Trate o prompt como um componente de software, equilibrando a balança entre **qualidade (precisão)**, **custo (tokens)** e **latência (tempo de resposta)**.