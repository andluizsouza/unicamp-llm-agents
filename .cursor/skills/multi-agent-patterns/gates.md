# Quando considerar cada peça

Não adicione peça por ser “o próximo passo”. Adicione porque o eval (ou o incremento da entrega) exige fechar uma classe de erro. O default do CLI passa a ser a versão do incremento; o baseline continua em `--arch`.

Catálogo, não sequência.

## Tools

**Sintoma:** o modelo inventa fatos que uma API/base já tem, ou precisa de uma ação.

**Obrigatório no incremento agêntico:** pelo menos uma tool que faça trabalho real (saída depende da entrada). Stub constante não conta.

**Não é motivo extra:** “quero ReAct” sem limitação medida.

Trate o retorno como dados não confiáveis. Logue chamadas e argumentos. Não engula exceção.

## RAG

**Sintoma:** contexto estoura, corpus muda, ou a versão atual não acha o trecho.

**Não é motivo:** vector store com corpus que cabe no prompt.

## MCP

**Sintoma:** a mesma integração copiada em ≥2 agentes/nós, ou fronteira de permissão.

**Não obrigatório** se uma tool local resolve. Justifique a escolha.

## Grafo (LangGraph)

Use quando o incremento pede fluxo de controle explícito, ou quando ramo/loop/retry não cabem num prompt.

| Padrão | Sintoma |
| :--- | :--- |
| Workflow (pipeline) | Etapas conhecidas de antemão |
| ReAct | A tool e a ordem não são fixas |
| Híbrido | Parte fixa + laço pontual |
| Roteador / reflexivo / supervisor | Só se o eval (ou a próxima entrega) exigir |

Sempre: estado, >1 etapa, decisão, **limite de passos**. Estouro = modo de falha.

## Memória

**Sintoma:** um turno posterior precisa do anterior, e a execução sem state falha. Demonstre essa falha.

**Não é motivo:** checkpoint “porque LangGraph tem”.

## Hard-stops

- `max_steps` / `recursion_limit`
- `max_tool_errors` consecutivos
- teto de tokens, tempo e custo
- efeitos irreversíveis sem humano

## Evidência no ADR

`run_id`, data, mesmo modelo, resultado (ganho / empate / piora) e hipótese. Empate ou piora **não** apagam a versão do incremento; impedem peças extras sem nova evidência.
