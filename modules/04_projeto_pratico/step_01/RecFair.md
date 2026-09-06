# **RecFair: Sistema de Recomendação Multiagentes com Auditoria de Viés e Claims**

**Disciplina**: INF0093 - Projeto Prático com Sistemas Multiagentes
**Documento**: Resumo da proposta do projeto prático
**Aluno**: Anderson Luiz Brandão de Souza

---

#### Tema e problema
A maioria dos sistemas de recomendação em e-commerce querem maximizar clique e conversão e, com isso, podem acabar reforçando viés de popularidade (poucos SKUs dominam a vitrine) e estereótipos quando o perfil do cliente é inferido ou perguntado de forma identitária. O RecFair quer tratar esse problema com um sistema multiagente incremental: não apenas sugerir produtos, mas recomendar, explicar com fonte, auditar justiça da exposição e recusar claim sem evidência. A conversão permanece um sinal de qualidade, nunca a função objetivo única.

#### O que o sistema deve fazer
O usuário descreve sua necessidade em linguagem natural (orçamento, restrição, ocasião, preferências). O estado da sessão guarda necessidade e restrições declaradas, e não demografia ou vieses sociais. Agentes especializados, orquestrados em grafo com estado compartilhado: (1) recuperação no catálogo (RAG); (2) ranqueamento com estoque e preço via ferramentas/MCP; (3) explicação com citação; (4) auditor de fairness (concentração de marca, estereótipo, disparidade de exposição em avaliação offline); (5) verificador de claims. O baseline é um pipeline testável (query → top-N citado). A complexidade cresce no padrão da disciplina: roteador de intenção, loop reflexivo (gerador + crítico) e supervisor multiagente. Extra (a definir se entra no escopo): interações e o desfecho da sessão (converteu / não converteu / abandonou a conversa) serão registrados para reavaliação offline e ajuste de skills e políticas — memória episódica e monitoramento.

#### Relação com o curso
A proposta aplica especificação de agentes (objetivo, ambiente, sensores, estado, tools, skills, métricas, autonomia com humano no loop), engenharia de prompts, RAG com *groundedness*, LangChain/LangGraph, MCP e skills procedimentais, planejamento e, no incremento final, auditoria em lote no estilo Deep Agent. A avaliação segue o bloco de qualidade e observabilidade: Precision/Recall do retrieval, fidelidade da explicação, diversidade da lista, paridade de exposição em personas sintéticas (atributos protegidos invisíveis ao ranker) e LLM-as-a-Judge — além de latência e custo.

#### Importância e diferencial
Recomendação é infraestrutura da indústria de varejo e marketplaces; o dano do viés é operacional (concentração de estoque), jurídico-reputacional (publicidade enganosa, claims ambientais) e social (exclusão de produtos e públicos). O RecFair pretende ser um exemplo de combate a viés algorítmico no ponto de decisão, não um classificador de fairness desconectado do produto. O diferencial frente a *personal shoppers* genéricos é o contrato duplo (utilidade + justiça) e a recusa explícita de completar o perfil do cliente com estereótipo. Dados: usar catálogo e políticas públicos ou sintéticos; sem PII real.

#### Como saberemos se é bom
Uso de um conjunto golden de sessões. Uma versão do projeto só é promovida se melhorar relevância das recomendações sem piorar diversidade, groundedness e alertas de claim. Disclaimer: humano aprova publicação de vitrine; o agente não executa compra real.