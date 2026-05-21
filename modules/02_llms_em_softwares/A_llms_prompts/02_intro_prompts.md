# Introdução à Engenharia de Prompt

## TL;DR / Resumo Executivo
O objetivo central deste bloco é transformar o desenvolvedor de um usuário casual em um **projetista de sistemas**, utilizando **prompts estruturados** para mitigar a natureza probabilística das LLMs. Através da Engenharia de Prompt, busca-se reduzir a variância das respostas e garantir a **interoperabilidade**, permitindo que a saída da IA seja consumida diretamente por sistemas de software via formatos como JSON.

## Conceitos Fundamentais
*   **Prompt:** Conjunto de sinais de entrada utilizados para condicionar o modelo a gerar uma resposta específica; funciona como o "volante" que guia o motor (modelo).
*   **Não-Determinismo:** Característica técnica onde LLMs, por serem sistemas probabilísticos, podem gerar saídas diferentes para a mesma entrada.
*   **Engenharia de Prompt:** Processo **disciplinado, iterativo e repetível** de design de instruções (escrever → testar → medir → refinar) para controlar o comportamento do modelo.
*   **Injeção de Conteúdo:** Técnica de inserir dados externos e privados (de bancos de dados ou documentos) diretamente no prompt para que a IA responda sobre informações que não estavam em seu treinamento original.
*   **Janela de Contexto:** Limite total de tokens (unidades de texto) que o modelo pode processar por vez, abrangendo a entrada e a saída.
*   **Lost in the Middle:** Fenômeno em que o modelo perde qualidade de processamento em informações localizadas no meio de prompts muito longos, priorizando o início e o fim do contexto.

## Matriz de Comparação ou Tabela

| Critério | Prompt Genérico | Prompt Estruturado |
| :--- | :--- | :--- |
| **Definição** | Instrução curta, vaga e sem contexto adicional. | Instrução detalhada com papel, tarefa e formato definidos. |
| **Exemplos** | "Fale sobre diabetes" ou "Explique machine learning". | "Você é médico. Explique diabetes para um idoso em 2 parágrafos". |
| **Como/Quando Usar** | Consultas rápidas e informais para usuários finais. | Integração em sistemas, automação e chatbots profissionais. |
| **Pontos Positivos** | Rapidez e simplicidade na escrita inicial. | Resultados **consistentes**, previsíveis e prontos para processamento via código. |
| **Pontos Negativos** | Alta variância, respostas "enciclopédicas" e dificuldade de automação. | Maior consumo de tokens (custo) e necessidade de refinamento constante. |

## Diagrama de Fluxo Lógico

O processo de criação e integração de um prompt em um sistema segue este fluxo estruturado para garantir qualidade e previsibilidade:

1.  **Definição da Persona (Papel):** Atribui uma identidade à IA (ex: "Você é um assistente de vendas") para guiar o tom e o domínio da resposta.
2.  **Declaração da Tarefa:** Define o objetivo claro e específico a ser executado pelo modelo.
3.  **Injeção de Dados/Contexto:** O sistema realiza uma consulta (ex: SQL) e insere informações externas no prompt para guiar a resposta.
4.  **Configuração de Formato (Output):** Exige uma saída específica, como **JSON**, para permitir que o software processe a informação (ex: via `json.loads()`).
5.  **Aplicação de Restrições e Exemplos:** Define o que não deve ser feito e fornece exemplos de **few-shot** (entrada/saída esperada) para aumentar a precisão.
6.  **Ciclo de Refinamento:** O desenvolvedor **testa, mede e refina** a instrução continuamente até atingir a consistência desejada para o sistema.