---
name: multi-agent-patterns
description: >-
  Define e evolui a arquitetura de um sistema multiagente (prompt, tools, RAG,
  MCP, LangGraph, registry, memória). Use ao criar agentes, tools, dados de RAG,
  servidores MCP, grafos ou ao promover complexidade.
---

# Padrões de sistemas multiagente

## Postura

Agent = Model + Harness. Harness = Context + Tools + Constrain + Verify + Correct.

Mantenha simples. Transparência (logs, estado, decisões). ACI pensada para o modelo. Implementação no **pacote Python + CLI**, não em notebook. Efeitos irreversíveis: humano no loop.

## Evolução

Não há escada fixa. Prompt, tools, RAG, MCP, workflow/grafo e multiagente são **peças**.

1. Baseline mais simples que resolve a tarefa.
2. Incremento vigente: a menor arquitetura que ataca as limitações medidas (e o que a entrega atual exigir, ex. estado explícito + ferramenta real + término).
3. Justifique a escolha: **workflow determinístico**, **ReAct**, ou **híbrido** — pelo problema, não pela moda.
4. Meça vs baseline (skill `agent-evaluation`), **mesmo modelo**, baseline reexecutado agora.
5. Default do CLI = incremento vigente. Empate/piora: relatados com hipótese; a versão **não** some do runtime.
6. Peças além do incremento: só com nova limitação medida.
7. ADR **datado**.

Gates: [gates.md](gates.md). Cada arquitetura: `id` + `date` + nome. Módulos separados; **não mute** o baseline.

## Catálogo de peças (sem ordem)

| Peça | Pergunta | Sinal de que pode valer |
| :--- | :--- | :--- |
| Prompt | Como responder nesta chamada? | Tarefa cabe em uma inferência |
| Tool local | O que posso *fazer* agora? | Fatos mutáveis ou ações que o modelo inventa |
| RAG | O que recuperar do corpus? | Conhecimento não cabe no contexto |
| MCP | Onde acesso padronizado? | Reuso por ≥2 agentes **ou** fronteira de segurança |
| Grafo | Como orquestrar estado e ramos? | Ramo, loop, retry, especialistas |
| Memória / checkpoint | O que persiste entre passos ou turnos? | O próximo passo depende do anterior |
| Skill procedimental | Como operar com política? | Tools existem, o procedimento falha |

**Tool boa:** trabalho **real** (a saída depende da entrada). Função que devolve constante **não** é tool. Schema Pydantic, descrição acionável, erro estruturado. Retorno da tool é **entrada não confiável** (risco de injeção): menor privilégio, logar nome+args.

**MCP:** não é obrigatório. Se não houver reuso nem fronteira, justifique tool local. Se houver reuso entre agentes/apps, considere MCP explicitamente.

RAG não substitui tool de fato mutável.

## Padrões de grafo (quando houver grafo)

Estado explícito. Pelo menos um fluxo com mais de uma etapa. Roteamento condicional **ou** seleção de tool **ou** outro mecanismo de decisão. Condição de término + **limite de passos** (`recursion_limit` / `max_steps`). Estouro do limite = modo de falha a registrar.

| Padrão | Quando |
| :--- | :--- |
| Pipeline (workflow) | Etapas fixas |
| Roteador | Intenções distintas |
| ReAct / loop agente–tool | Decisão dinâmica de tool |
| Reflexivo | Gerador + crítico com parada |
| Supervisor | Especialistas com tools disjuntas |

Esqueleto: [langgraph.md](langgraph.md).

## Harness

- **Constrain:** allowlist, tetos, políticas; tool output ≠ instrução.
- **Verify:** schema e invariantes em código.
- **Correct:** retry com erro estruturado; senão abster e registrar. Erro de tool **não** pode ser silencioso.

## Memória e contexto

- Curto prazo = state / checkpointer da sessão (`thread_id` para isolamento).
- Se alegar memória conversacional: mostre **primeiro** a mesma interação **sem** o contexto anterior (a falha justifica o incremento).
- Se memória conversacional não couber: explique qual estado a execução precisa preservar (documento, ids, parciais, plano, tool calls).
- Conversas longas: medir crescimento de tokens e estratégia (recorte, resumo, retrieval).
- Longo prazo só com ADR datado.

## Checklist

```
- [ ] Código no pacote; CLI executa a versão; notebook só chama
- [ ] Arquitetura id + data; baseline intacto
- [ ] ADR datado
- [ ] Tools reais; retornos tratados como não confiáveis; chamadas logadas
- [ ] Término + limite de passos
- [ ] Eval vs baseline, mesmo modelo; ganho/empate/piora relatado
```
