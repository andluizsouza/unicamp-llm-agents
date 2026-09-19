# UNICAMP - INF0093 - PROJETO PRÁTICO COM SISTEMAS MULTIAGENTES - 2S 2026

**Prof. Marcelo da Silva Reis** (msreis@unicamp.br)

## Entregável 3: Sistema Multiagente
*Campinas, 11 de setembro de 2026*

---

### Sumário
1. Objetivo
2. Formato
   - 2.1 Como partir do Entregável 2
   - 2.2 Alternativa: entrega com repositório
   - 2.3 Estrutura herdada
3. Evolução da arquitetura
   - 3.1 Divisão em agentes
   - 3.2 Padrão de organização
   - 3.3 Contrato entre agentes
   - 3.4 Skills e planejamento
   - 3.5 Observabilidade
4. Comparação com a v2
   - 4.1 Novos modos de falha
5. Análise arquitetural
   - 5.1 Pergunta obrigatória
6. Entrega do notebook
7. Critérios de avaliação

---

## 1. Objetivo
O terceiro entregável transforma a v2 em um sistema com mais de um agente. A divisão precisa nascer de uma limitação observada na versão anterior, e não da vontade de usar a técnica. Vale lembrar que adicionar agentes tem custo: cada agente acrescenta chamadas ao modelo, uma passagem de contexto que pode perder informação e um ponto de decisão que pode errar. O que será avaliado é a qualidade da investigação sobre esse compromisso, não a quantidade de agentes.

## 2. Formato
* Grupos de 1-3 estudantes, mantendo a mesma composição dos entregáveis anteriores.
* Entrega em notebook Jupyter (`.ipynb`), com saídas salvas.
* Documentação em Markdown e código em Python.
* Código executável, com instruções de configuração.

### 2.1 Como partir do Entregável 2
1. Renomeie o arquivo de template para `E3_sobrenomes.ipynb`;
2. Consolide o bloco de estrutura herdada das versões anteriores;
3. Acrescente as seções novas exigidas por este entregável.

### 2.2 Alternativa: entrega com repositório
Assim como no Entregável 2, se o sistema necessitar de recursos que inviabilizem o uso exclusivo do Jupyter notebook, pode-se adicionalmente entregar um arquivo zip contendo o código-fonte executável por linha de comando junto ao notebook `.ipynb` preenchido.

### 2.3 Estrutura herdada
A v2 deve ser reexecutada nesta entrega, com o mesmo modelo e no mesmo ambiente da v3. Trocar o modelo entre as versões impede atribuir a diferença observada à arquitetura.

## 3. Evolução da arquitetura

### 3.1 Divisão em agentes
O sistema deve ter pelo menos dois agentes com responsabilidades distintas. Para cada um, informe:
1. o escopo, com a fronteira explícita do que ele não faz;
2. as ferramentas de que dispõe;
3. a instrução que recebe;
4. o critério pelo qual seria avaliado isoladamente.

Se uma responsabilidade não puder ser descrita nesses quatro itens, provavelmente ela ainda é uma etapa de fluxo e não um agente. Nesse caso, mantenha-a como etapa e explique a decisão: reconhecer que a divisão não se justifica é um resultado legítimo, desde que sustentado por evidência da v2.

### 3.2 Padrão de organização
Escolha e justifique o padrão adotado, considerando o problema e não a tecnologia:
* **supervisor**, quando a escolha do próximo passo depende da entrada;
* **pipeline**, quando a ordem das etapas é conhecida de antemão;
* **transferência entre pares**, quando cada agente sabe melhor que um terceiro quem deve seguir;
* **outra organização**, descrita explicitamente.

### 3.3 Contrato entre agentes
Descreva o que trafega entre os agentes. Resultados estruturados atravessam melhor do que texto livre, e a evidência que sustenta uma conclusão deve estar junto com ela. Um sinal de contrato mal definido é o agente final precisar reler a fonte original para entender o que os demais produziram.

Informe também o que cada agente enxerga do contexto: tudo, apenas a sua fatia, ou a sua fatia acompanhada de um resumo. Essa decisão costuma explicar boa parte da diferença de qualidade e de custo entre as versões.

### 3.4 Skills e planejamento
Estes dois recursos são exigidos apenas quando o problema os justificar. Adote-os se houver motivo, e explique a decisão em qualquer caso.

* **Skills:** instruções e ferramentas organizadas por capacidade, com a instrução completa carregada apenas quando a capacidade é escolhida. Útil quando o prompt de um agente acumula instruções para casos que raramente ocorrem.
* **Planejamento explícito:** a sequência de passos é escrita antes da execução, e vira um artefato que pode ser lido e avaliado. Útil quando a tarefa tem partes independentes ou quando errar a ordem custa caro. Se houver replanejamento, registre o plano inicial e o final.

### 3.5 Observabilidade
A execução deve produzir um registro que permita responder a três perguntas: por que o sistema tomou aquele caminho, onde a informação correta se perdeu, e qual etapa dominou custo e latência. Registre, no mínimo, quais agentes foram acionados e em que ordem, as decisões de roteamento com sua justificativa, as chamadas a ferramentas com seus argumentos, e latência e número de chamadas ao modelo por agente. Um total agregado do sistema inteiro não atende ao requisito, pois não indica onde intervir.

## 4. Comparação com a v2
Compare v2 e v3 na mesma régua congelada de testes.

### 4.1 Novos modos de falha
Identifique novos modos de falha introduzidos pela arquitetura multiagente:
* encaminhamento para o especialista errado pelo orquestrador;
* atuação de especialista fora de seu escopo;
* perda ou corrupção de dados na passagem de contexto entre agentes;
* laços de transferência sem convergência que esgotam o limite de recursão.

## 5. Análise arquitetural
Discuta:
* quais limitações da v2 foram resolvidas;
* quais limitações permaneceram ou surgiram;
* se algum agente poderia voltar a ser uma etapa de fluxo;
* que evidência do trace sustenta cada afirmação acima.

### 5.1 Pergunta obrigatória
Ao final do notebook, responda:
> **Qual das versões construídas até aqui você levaria para uso real, e que evidência ainda falta para sustentar essa escolha?**

A resposta será o ponto de partida do Entregável 4.

## 6. Entrega do notebook
A entrega do `.ipynb` deverá ser feita até o dia **20 de setembro**, utilizando o Google Classroom da disciplina. O notebook deve ser executado do início ao fim e salvo com as saídas visíveis; todavia, se você estiver tendo problemas com limite de tokens no Groq, você pode rodar uma célula de código por vez, sem utilizar o "run all" do Jupyter notebook. Nenhuma chave de API deve estar escrita no notebook.

## 7. Critérios de avaliação

| Critério | Peso |
| :--- | :---: |
| Justificativa da divisão a partir de limitações da v2 | 20% |
| Arquitetura multiagente e uso adequado de LangGraph | 25% |
| Contrato entre agentes e gerenciamento de contexto | 15% |
| Observabilidade e atribuição de custo | 15% |
| Comparação experimental com a v2 | 15% |
| Análise arquitetural, documentação e reprodutibilidade | 10% |

---