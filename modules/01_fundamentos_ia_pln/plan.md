# Plano: Fine-Tuning SFT com QLoRA — Atividade Avaliativa

Ajuste fino do `google/gemma-3-1b-pt` usando QLoRA 4-bit no dataset `HuggingFaceTB/smoltalk2` (split multilingual, filtrado para português + amostragem), executável no Google Colab gratuito (T4 16GB). Inclui comparação base vs ajustado e seção bônus de DPO.

---

### **Fase 1: Configuração e Exploração** (Steps 1–3)

1. **Setup do ambiente** — Instalar `transformers`, `datasets`, `peft`, `trl`, `bitsandbytes`, `accelerate`, `huggingface_hub`. Verificar GPU, login HuggingFace. Bloco markdown inicial com descrição da tarefa e decisões de arquitetura.

2. **Exploração e filtragem do dataset** — Carregar `smoltalk2/SFT/smoltalk_multilingual_8languages_lang_5_no_think` (254k rows) em modo **streaming**. Inspecionar schema e exemplos. **Filtrar por idioma português** (detectar idioma no conteúdo das mensagens com heurística ou `langdetect`). Depois, **amostrar ~2000–3000 exemplos** para caber no T4. Salvar localmente para evitar re-download. *Documentar a estratégia de filtragem e justificar tamanho da amostra.*

3. **Análise de tokens** — Aplicar `tokenizer.apply_chat_template()` em cada exemplo, calcular distribuição de comprimentos (min, mediana, max, percentis). Definir `max_length` (~512). Gerar histograma. *Justificar com dados concretos.*

> **Verificação**: Dataset filtrado e salvo. Distribuição de tokens calculada. `max_length` definido.

---

### **Fase 2: Modelo Base e Baseline** (Steps 4–6)

4. **Configuração de quantização** — `BitsAndBytesConfig` com 4-bit NF4, double quantization, bfloat16. *Documentar: o que é QLoRA, por que NF4, redução ~8x em memória.*

5. **Carregar modelo e tokenizer** — Base: `google/gemma-3-1b-pt` (quantizado). Tokenizer: `google/gemma-3-1b-it` (tem chat_template). Demonstrar `apply_chat_template` com exemplo. *Explicar por que separar PT/IT.*

6. **Geração baseline** — Definir 3–5 prompts variados em português. Gerar respostas com modelo base (sem fine-tuning). Guardar resultados. *Mostrar que o modelo base apenas completa texto, sem seguir instruções.*

> **Verificação**: Modelo carregado em 4-bit. Chat template funcional. Baseline salvo.

---

### **Fase 3: Fine-Tuning SFT com QLoRA** (Steps 7–9, *depende de Fase 1 e 2*)

7. **LoRA config** — `r=16`, `lora_alpha=16`, `dropout=0.05`, `target_modules="all-linear"`, `modules_to_save=["lm_head", "embed_tokens"]`. Imprimir parâmetros treináveis (~1–5% do total, redução ~99%). *Documentar cada parâmetro com referência à teoria (rank, scaling, etc.).*

8. **SFT config** — `max_length=512`, `packing=True`, `epochs=1`, `batch=2`, `grad_accum=4` (efetivo=8), `gradient_checkpointing=True`, `optim="paged_adamw_8bit"`, `lr=2e-4`, `warmup=100`, `bf16=True`, `max_grad_norm=0.3`. *Documentar packing, gradient checkpointing, gradient accumulation.*

9. **Executar treinamento** — `SFTTrainer.train()`. Monitorar loss. ~30–60 min no T4. Salvar checkpoint.

> **Verificação**: Loss decrescente. Checkpoint salvo. Parâmetros treináveis << total.

---

### **Fase 4: Avaliação e Comparação** (Steps 10–12, *depende de Fase 3*)

10. **Carregar modelo ajustado** — **Reiniciar kernel** (liberar VRAM). Carregar base + adapters LoRA do checkpoint.

11. **Comparação lado a lado** — Mesmos prompts do Step 6. Respostas do modelo ajustado vs baseline. Tabela comparativa + análise qualitativa. Testar também prompts fora do domínio. *O modelo ajustado deve seguir instruções e responder em formato de chat.*

12. **Upload ao HuggingFace Hub** — `push_to_hub()` para modelo e tokenizer.

> **Verificação**: Respostas qualitativamente melhores. Upload com sucesso.

---

### **Fase 5 (Bônus): DPO** (Steps 13–15, *depende de Fase 4*)

13. **Dataset de preferências** — Carregar subset `Preference` do smoltalk2. Filtrar pt + amostrar ~500–1000. Formato: prompt + chosen + rejected.

14. **Treinar com DPO** — `DPOTrainer`, `beta=0.1`, 1 época. *Documentar DPO vs RLHF.*

15. **Comparação final** — Base vs SFT vs DPO nos mesmos prompts. Tabela + análise.

---

### **Arquivos de referência**
- hands_on_finetune_v1.ipynb — Pipeline completo SFT: `BitsAndBytesConfig`, `LoraConfig`, `SFTConfig`, `SFTTrainer`, `create_conversation()`, `count_tokens_in_split()`
- hands_on_finetune_v2.ipynb — Versão com streaming + `islice` + `Dataset.from_list()`
- hands_on_dataset.ipynb — Exploração do smoltalk2 com streaming
- 02_conceitos_finetune.md — Teoria QLoRA, LoRA, DPO (base para documentação)
- 03_pratica_finetune.md — Pipeline prático SFT + DPO

### **Verificação final**
1. Executar o notebook completo no Colab (Runtime → Run all) sem erros
2. Confirmar que a loss é decrescente durante o treino
3. Confirmar visualmente que respostas do modelo ajustado são superiores ao baseline
4. Validar que todos os blocos de código são precedidos por blocos markdown explicativos
5. Confirmar upload no HuggingFace Hub

### **Escopo**
- **Incluso**: SFT com QLoRA, filtragem por idioma, análise de tokens, comparação qualitativa, upload HF, DPO bônus
- **Excluído**: Métricas automáticas (BLEU, ROUGE), benchmark formal, treino em múltiplas GPUs

---

Revise o plano e me diga se quer ajustar algo antes da implementação.