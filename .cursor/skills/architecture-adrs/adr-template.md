# Template ADR

```markdown
# ADR NNNN: Título curto em português

- Status: proposto | aceito | rejeitado | substituído por ADR NNNN
- Data: YYYY-MM-DD
- Arquitetura: `<id>` (baseline permanece `<id-anterior>`)
- Autores:

## Contexto

Limitação observada. Cite resultado de eval, `run_id` e o que a arquitetura vigente já faz.

## Opções

### A — Permanecer como está
Prós / contras.

### B — Opção proposta
Prós / contras (complexidade, custo, latência, eval).

### C — Alternativa realista

## Decisão

Escolhemos ___. Entra no código agora: ___. Fica fora: ___.

Se o eval empatar ou piorar, registre hipótese. O incremento vigente **permanece** executável (default do CLI). Não acrescente peças extras sem nova evidência.

## Consequências

- Contratos / schemas
- Hard-stops
- O que o eval passa a cobrir (sem listar fórmulas aqui se o projeto ainda não as definiu)
- Risco (custo, falha, governança)

## Evidência / reavaliação

- Hipótese: ...
- Experimento: golden-set revisão `...`, notebook `eval/notebooks/...`
- Reavaliar até: YYYY-MM-DD
```

Nome do arquivo: `NNNN-titulo-em-kebab.md`. A primeira decisão do app: `0001-baseline.md`, com data.
