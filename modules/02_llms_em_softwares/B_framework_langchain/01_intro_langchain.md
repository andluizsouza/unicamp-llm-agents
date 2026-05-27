# Introdução ao LangChain: Orquestração de Sistemas com LLMs

## TL;DR / Resumo Executivo
O **LangChain** é um framework de código aberto projetado para permitir a construção de **sistemas de software robustos**, indo além de simples prompts isolados. Ele atua como um "maestro" que coordena LLMs, ferramentas externas e memória, permitindo que a aplicação responda com base no que o modelo **sabe** (treinamento), no que ele **busca** (APIs e bancos de dados) e no que ele **lembra** (histórico), mitigando alucinações e contextualizando as respostas para o mundo real.

## Conceitos Fundamentais
*   **LangChain:** Framework para desenvolvimento de aplicações baseadas em LLMs, focado em orquestração e modularização.
*   **Chains:** Sequências de passos que definem o fluxo de execução do sistema.
*   **Tools:** Funções externas (como busca em SQL ou APIs) que o modelo pode decidir chamar para obter dados em tempo real.
*   **Memory:** Persistência de estado que guarda o contexto do chat para interações futuras.
*   **Agents:** Sistemas que usam o LLM como um "raciocinador" para decidir dinamicamente quais ações tomar, em vez de seguir um fluxo fixo.
*   **LCEL (LangChain Expression Language):** Linguagem declarativa que utiliza o operador **pipe (`|`)** para compor cadeias de forma modular e legível.
*   **RAG (Retrieval-Augmented Generation):** Padrão que fornece dados externos ao LLM (como PDFs ou bancos vetoriais) para enriquecer o prompt antes da geração da resposta.

## Matriz de Comparação

### Frameworks de Orquestração
| Framework | Definição | Exemplo de Uso | Quando Usar | Pontos Positivos | Pontos Negativos |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LangChain** | Orquestrador geral e modular. | Chatbots complexos e agentes autônomos. | Sistemas com múltiplos passos e dependências externas. | Ecossistema vasto (+700 integrações) e flexibilidade. | Curva de aprendizado alta e instabilidade em mudanças de versão. |
| **LlamaIndex** | Focado em estrutura de dados e RAG. | Sistemas de busca em documentos massivos. | Projetos onde a recuperação de dados é a prioridade central. | RAG avançado nativo e curva de aprendizado menor que LangChain. | Menos maduro para agentes complexos comparado ao LangChain. |
| **Semantic Kernel** | Orquestrador mantido pela Microsoft. | Integração de LLMs em sistemas corporativos C#. | Ambientes empresariais já integrados ao Azure/Microsoft. | Excelente suporte para C#, Java e stacks Microsoft. | Comunidade menor em Python comparada ao LangChain. |

### Estratégias de Memória
| Tipo | Funcionamento | Custo de Tokens | Ideal Para |
| :--- | :--- | :--- | :--- |
| **ConversationBuffer** | Mantém todo o histórico da conversa. | Alto (cresce infinitamente). | Conversas curtas ou onde o contexto total é crítico. |
| **ConversationWindow** | Guarda apenas as últimas **N** mensagens. | Controlado/Fixado. | Chatbots que precisam de contexto imediato sem estourar o limite de tokens. |
| **ConversationSummary** | Resume o histórico utilizando um LLM. | Médio. | Longas interações onde o histórico completo seria custoso demais. |

## Diagrama de Fluxo Lógico (Pipeline React)

O processo de execução de um **Agente** ou sistema orquestrado segue o ciclo **ReAct (Reasoning and Acting)**:

1.  **Input (Entrada):** O usuário envia uma requisição (ex: "Qual o frete para o CEP X?").
2.  **Thought (Pensamento):** O modelo analisa a pergunta e decide o que fazer com base nas ferramentas disponíveis.
3.  **Action (Ação):** O modelo escolhe uma ferramenta (ex: `calcular_frete`) e gera os argumentos necessários.
4.  **Observation (Observação):** O framework (LangChain) executa a ferramenta (chama a API dos Correios) e retorna o resultado bruto para o modelo.
5.  **Refinement (Refinamento):** O modelo avalia se a observação é suficiente para responder ao usuário. Se não for, ele volta ao passo de **Pensamento**.
6.  **Final Answer (Resposta Final):** O modelo consolida os dados e gera uma resposta em linguagem natural adequada ao contexto.

**Regra Prática:** Se o seu sistema pode ser resolvido com menos de **50 linhas de código** sem o framework, evite usar o LangChain para não adicionar complexidade desnecessária.