# Template de notebook de relatório

Arquivo típico: `eval/notebooks/compare_<architecture_id>_vs_baseline.ipynb` (ou o nome exigido pela entrega).

O notebook **não** contém o sistema. Células de código só: imports do pacote, chamadas (`run_eval(...)`, `load_run(...)`), e apresentação.

## Ordem

1. **Título, hipótese, ADR** — o que a candidata deveria resolver no baseline.
2. **Como reproduzir** — `make install-dev`, `make kernel`, `make chat ARCH=baseline`; golden-set via `run_eval` nas células abaixo.
3. **Estrutura herdada (import)** — esquema de saída, golden-set + hash, funções de verify, campos de registro de run. Sem colar a implementação.
4. **Setup** — `git_sha`, modelo (o **mesmo** nas duas versões), `prompt_version`, `golden_revision`. Sem chaves.
5. **Golden-set** — `len(cases)`; acréscimos; se houve correção de defeito, o que e por quê.
6. **Execução** — `run_eval(arch="baseline", persist=True)` (e candidata, se comparando). Pode reler `eval/runs/` da mesma sessão.
7. **Tabela por caso** — id + colunas do projeto + latência, `llm_calls`, `tool_calls`.
8. **Eixos da comparação** — qualidade, tarefas compostas, informação ausente, custo de chamadas, latência; modos de falha novos (se houver).
9. **Interpretação** — ganho, empate ou piora, com hipótese. Sem generalizar com n pequeno.
10. **Análise arquitetural** — o que o baseline não resolvia e agora resolve; o que restou; o que surgiu; acoplamentos; candidata a agente especializado na próxima versão.
11. **Limitações da medida**.

Regras: `pandas` para tabelas; medição só via pacote `eval/`; ipynb salvo **com outputs**.
