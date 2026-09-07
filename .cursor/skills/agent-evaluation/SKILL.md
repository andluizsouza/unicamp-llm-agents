---
name: agent-evaluation
description: >-
  Constrói e mantém avaliação de sistemas multiagente: golden-set (só cresce),
  runner no pacote, comparação com baseline e notebooks que só invocam o
  pacote. Use ao criar ou alterar casos, o runner, relatórios Jupyter ou
  interpretar ganho/empate/piora.
---

# Evaluation de sistemas multiagente

## Onde corre a eval

A medição é código do pacote (`src/<package>/eval/`), disparada por CLI (`make eval ARCH=...`). O notebook **não** reimplementa verify, métricas nem o agente: importa e chama, ou lê `eval/runs/*.json` gerados pelo CLI.

## Golden-set

Régua compartilhada. Casos escritos **antes** de tunar prompts.

- Casos antigos: **não modificar nem remover**.
- **Acréscimo** permitido (tamanho e escopo só aumentam).
- **Exceção — defeito real:** caso mal formulado, rótulo/referência errada, ou verificação que não mede o que pretendia. Corrija, **registre o que mudou e por quê**, reexecute baseline e versão atual.
- Impressão digital (hash) do conjunto em cada run (`golden_revision`), para ver se a régua mudou entre entregas.

Local: `data/golden/`. Esquema dos casos e as métricas são **do projeto**. Esta skill exige: id estável, comparação justa, instrumentação.

**Herdado entre versões (sem alteração na comparação principal):** funções de verificação, critérios de sucesso, formato de saída.

## Mesmo experimento

- Reexecute o baseline **nesta** sessão, no **mesmo modelo** e ambiente da candidata.
- Não troque de modelo junto com a arquitetura — a diferença ficaria inexplicável.
- A comparação principal usa os casos da régua original; casos novos ilustram capacidades novas, à parte.

## Instrumentação

`eval/runs/<run_id>.json`: `run_id`, `architecture_id`, `architecture_date`, `git_sha`, `model`, `model_version`, `temperature`, `prompt_version`, `golden_revision` (hash), `started_at`; por caso: `latency_s`, `llm_calls`, `tool_calls`, `tokens_in`, `tokens_out`, `cost_usd`, saída estruturada, erros / halt_reason.

## O que comparar (eixos, não fórmulas)

O projeto define as medidas. Toda comparação baseline vs candidata cobre pelo menos:

- qualidade / correção
- tarefas compostas
- informação ausente
- nº de chamadas ao LLM e às tools
- latência
- **modos de falha novos** da versão agêntica, quando ocorrerem: tool certa com arg errado; tool desnecessária; tool necessária não chamada; erro de tool silencioso; laço cortado pelo limite de passos; resposta que ignora o retorno da tool

Com poucos casos, prefira “a v2 acertou o caso X que a v1 errava” a “a v2 é melhor”. Empate ou piora é resultado **válido** se vier com hipótese. Rubrica humana, se houver, explícita no relatório.

## Notebook

Relatório da entrega: Markdown (hipótese, análise, pergunta de especialização da próxima versão) + células que só invocam o pacote. Estrutura: [notebook-template.md](notebook-template.md). Executado, saídas salvas, sem API keys.

## Métodos (não métricas)

Determinístico, rubrica humana (amostra), LLM-as-judge (modelo ≠ gerador, temperatura 0, justificativa, calibração). Se a limitação for da medida, registre — não encolha o golden-set.
