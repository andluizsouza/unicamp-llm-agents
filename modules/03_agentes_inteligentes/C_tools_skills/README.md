# Seção C: Tools, MCP e Skills para Agentes Inteligentes

## TL;DR / Resumo Executivo
Esta seção apresenta os blocos que transformam um LLM em um agente mais completo e operacional. O foco é mostrar como ferramentas permitem que o agente execute ações externas, como o Model Context Protocol (MCP) padroniza o acesso a recursos e integrações, e como skills encapsulam conhecimento especializado e procedimentos para orientar o comportamento do agente de forma consistente, segura e reutilizável.

## Conceitos Fundamentais (Tópicos Abordados)

- **Tools e integrações**: definição de ferramentas como extensões de capacidade do agente para acessar dados atualizados, executar operações e interagir com sistemas externos.
- **Tool calling**: o agente decide quando e qual ferramenta chamar, enquanto a aplicação executa a ação e devolve o resultado ao modelo.
- **MCP**: protocolo aberto para padronizar a conexão entre agentes, recursos, prompts e ferramentas, reduzindo a fragmentação de integrações.
- **Skills**: unidades modulares de conhecimento procedural que orientam o agente sobre como realizar tarefas específicas em contextos mais complexos.
- **Arquitetura de agentes**: combinação de tools, MCP e skills como base para construir sistemas mais robustos, governáveis e escaláveis.
- **Prática aplicada**: notebooks que ilustram, de forma didática, como esses conceitos podem ser implementados em exemplos reais.

![](tools_mcp_skills.png)


## Matriz de Conteúdo

| Aula | Tema Principal | Descrição Curta | Objetivo | Arquivo de Referência |
|------|----------------|----------------|----------|--------|
| 01 | Tools e Integrações | Introdução ao conceito de ferramentas, suas categorias, anatomia e padrões de uso em agentes com LLMs. | Mostrar como um agente pode ampliar suas capacidades através de ações externas e interfaces bem definidas. | [01_tools.md](01_tools.md) |
| 02 | Model Context Protocol (MCP) | Apresentação do MCP como camada de padronização para acesso a recursos, prompts e ferramentas em arquiteturas de agentes. | Ensinar o papel do MCP na interoperabilidade, descoberta de capacidades e organização de integrações. | [02_mcp.md](02_mcp.md) |
| 03 | Skills de Agentes | Conceito de skills como pacotes de conhecimento especializado e procedimentos operacionais para orientar agentes em tarefas específicas. | Demonstrar como encapsular conhecimento procedural para melhorar consistência, reutilização e governança. | [03_skills.md](03_skills.md) |
| Prática | Ferramentas em Agentes | Notebook prático sobre tool calling, execução de ferramentas e construção de loops ReAct com LangChain e LangGraph. | Familiarizar o aluno com a lógica de chamar ferramentas e integrar ações ao raciocínio do agente. | [hands_on_tools.ipynb](hands_on_tools.ipynb) |
| Prática | MCP em Ação | Notebook com uma simulação didática do protocolo MCP, incluindo recursos, prompts, tools e um mini-servidor/cliente. | Mostrar como padronizar o acesso a capacidades externas em uma arquitetura de agente. | [hands_on_mcp.ipynb](hands_on_mcp.ipynb) |
| Prática | Skills Reutilizáveis | Notebook dedicado à modelagem de skills, descoberta e ativação, e integração com um agente em LangGraph. | Explorar como skills podem organizar conhecimento e procedimentos para tarefas mais complexas. | [hands_on_skills.ipynb](hands_on_skills.ipynb) |

![](full_system.png)
