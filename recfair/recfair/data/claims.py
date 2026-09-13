"""Synthetic product claims inspired by boticario.com.br (Sep 2026)."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from recfair.config import data_dir
from recfair.data.catalog import CATALOG

CLAIM_TYPES = ("publico_alvo", "descricao", "como_usar", "beneficios", "restricoes")
CLAIM_FIELDS = ("cod_sku", "claim_type", "claim_text")
CAPTURED_AT = "2026-09-13"
BOTICARIO_BASE = "https://www.boticario.com.br"

_CLAIMS_BY_SKU: dict[str, dict[str, str]] = {
    "1M9T5B": {
        "publico_alvo": "Mulheres modernas que buscam uma assinatura olfativa marcante e empoderada.",
        "descricao": "Her Code Eau de Parfum com notas florientais, frutadas e base amadeirada sensual.",
        "como_usar": "Aplicar generosamente em pontos de pulsação antes de sair para a noite.",
        "beneficios": "Alta fixação noturna com fragrância intensa, sofisticada e de longa permanência.",
        "restricoes": "Produto inflamável. Uso externo. Não ingerir.",
    },
    "24A51X": {
        "publico_alvo": "Pessoas que buscam hidratação corporal leve com fragrância suave e agradável.",
        "descricao": "Loção hidratante Cuide-se Bem Nuvem com textura aerada e perfume delicado de algodão.",
        "como_usar": "Aplicar sobre a pele limpa e seca após o banho, massageando até completa absorção.",
        "beneficios": "Hidratação por até 48 horas, fórmula vegana e textura de rápida absorção sem oleosidade.",
        "restricoes": "Uso externo. Evitar contato com olhos e mucosas.",
    },
    "2C8L4P": {
        "publico_alvo": "Mulheres jovens que preferem fragrâncias docemente frutadas e divertidas.",
        "descricao": "Egeo Dolce Desodorante Colônia com notas frutadas, florais e acentos gourmand.",
        "como_usar": "Pulverizar após banho em pulsos e pescoço.",
        "beneficios": "Fragrância jovem e vibrante com sensação refrescante.",
        "restricoes": "Evitar contato com olhos. Uso externo.",
    },
    "2M7K4F": {
        "publico_alvo": "Homens sofisticados que buscam uma fragrância fresca e contemporânea.",
        "descricao": "Zaad Eau de Parfum com notas cítricas, aquáticas e base amadeirada moderna.",
        "como_usar": "Borrife sobre pontos de pulsação após o banho, sem esfregar.",
        "beneficios": "Fragrância vibrante com excelente projeção e sensação de frescor prolongado.",
        "restricoes": "Produto inflamável. Manter longe de fontes de calor e chamas.",
    },
    "2Y8N4T": {
        "publico_alvo": "Pessoas com cabelos lisos que desejam prolongar o efeito liso e alinhado.",
        "descricao": "Shampoo Match Liso Prolongado com tecnologia anti-umidade e alinhamento dos fios.",
        "como_usar": "Aplicar nos cabelos molhados, massagear e enxaguar. Use regularmente.",
        "beneficios": "Prolonga o efeito liso, reduz volume indesejado e facilita a escovação.",
        "restricoes": "Evitar contato com olhos. Uso externo.",
    },
    "3G7P2W": {
        "publico_alvo": "Cabelos oleosos ou com buildup que precisam de limpeza detoxificante.",
        "descricao": "Shampoo Cuide-se Bem Feira Vinagre de Framboesa com vinagre de framboesa e limpeza profunda.",
        "como_usar": "Massagear no couro cabeludo e comprimento dos cabelos molhados. Enxágue bem.",
        "beneficios": "Remove impurezas e excesso de oleosidade, deixando fios leves e brilhantes.",
        "restricoes": "Uso externo. Evitar contato com olhos.",
    },
    "3R1B6M": {
        "publico_alvo": "Homens exigentes que valorizam exclusividade e perfumaria de alta perfumaria.",
        "descricao": "Malbec Signature Eau de Parfum com blend refinado de notas amadeiradas e especiarias nobres.",
        "como_usar": "Aplicar sobre pele hidratada em pontos estratégicos para intensificar a projeção.",
        "beneficios": "Assinatura olfativa única com longa permanência e sofisticação marcante.",
        "restricoes": "Uso externo. Em caso de irritação, suspenda o uso e consulte um dermatologista.",
    },
    "4W6J2P": {
        "publico_alvo": "Pessoas que preferem sabonete líquido cremoso com fragrância sofisticada.",
        "descricao": "Sabonete líquido Nativa SPA Orquídea Noire com fórmula cremosa e perfume floral intenso.",
        "como_usar": "Aplicar na pele molhada, massagear até formar espuma e enxaguar abundantemente.",
        "beneficios": "Limpeza delicada com fragrância envolvente e sensação de pele macia.",
        "restricoes": "Uso externo. Evitar contato com olhos.",
    },
    "5J8P2X": {
        "publico_alvo": "Homens jovens e modernos que preferem fragrâncias intensas e contemporâneas.",
        "descricao": "Malbec Club Intenso Desodorante Colônia com perfil amadeirado-aromático e notas vibrantes.",
        "como_usar": "Aplicar generosamente nas regiões corporais após higienização diária.",
        "beneficios": "Fixação intensa ideal para momentos sociais e uso noturno.",
        "restricoes": "Uso externo. Não aplicar em pele sensibilizada ou com dermatites.",
    },
    "5X3R8K": {
        "publico_alvo": "Mulheres que apreciam fragrâncias gourmand e envolventes.",
        "descricao": "Coffee Woman Seduction Desodorante Colônia com notas de café, baunilha e flores.",
        "como_usar": "Aplicar sobre pele limpa em regiões de pulsação.",
        "beneficios": "Fragrância sedutora e adocicada com boa fixação para momentos especiais.",
        "restricoes": "Uso externo. Evitar contato com mucosas.",
    },
    "6D2W9K": {
        "publico_alvo": "Homens que preferem fragrâncias ousadas com perfil amadeirado-especiado.",
        "descricao": "Clash Desodorante Colônia com acordes intensos de madeira, couro e especiarias.",
        "como_usar": "Borrife sobre pele seca após banho, evitando áreas sensibilizadas.",
        "beneficios": "Personalidade olfativa forte com fixação prolongada para uso diário.",
        "restricoes": "Produto inflamável. Não ingerir. Uso externo.",
    },
    "6P8H3A": {
        "publico_alvo": "Mulheres jovens que buscam fragrância vibrante e romântica.",
        "descricao": "Floratta Red Desodorante Colônia com notas frutadas, florais e acentos adocicados.",
        "como_usar": "Aplicar sobre pele limpa após o banho em pulsos e pescoço.",
        "beneficios": "Fragrância feminina e sedutora com boa projeção para o dia a dia.",
        "restricoes": "Uso externo. Manter fora do alcance de crianças.",
    },
    "7H5A2E": {
        "publico_alvo": "Mulheres que desejam hidratação corporal com a fragrância icônica Lily.",
        "descricao": "Loção hidratante Lily com perfume floral sofisticado e textura sedosa.",
        "como_usar": "Aplicar diariamente sobre pele limpa após o banho, massageando suavemente.",
        "beneficios": "Hidratação prolongada com fragrância elegante; fórmula suave indicada também para pele sensível.",
        "restricoes": "Uso externo. Suspender uso em caso de irritação.",
    },
    "7K2N9A": {
        "publico_alvo": "Homens que buscam uma fragrância marcante e sofisticada para o dia a dia.",
        "descricao": "Desodorante colônia Malbec com notas amadeiradas, especiadas e acentuadas de vinho tinto.",
        "como_usar": "Aplicar sobre a pele limpa e seca, especialmente nas regiões do pulso, pescoço e tórax.",
        "beneficios": "Fragrância intensa de longa duração com fixação prolongada e sensação refrescante.",
        "restricoes": "Uso externo. Evitar contato com os olhos e mucosas. Manter fora do alcance de crianças.",
    },
    "8K2F6Q": {
        "publico_alvo": "Mulheres sofisticadas que buscam uma fragrância floral elegante para ocasiões especiais.",
        "descricao": "Lily Eau de Parfum com bouquet de flores brancas, jasmim e acordes amadeirados suaves.",
        "como_usar": "Aplicar em pontos de pulsação: pulsos, pescoço e atrás das orelhas.",
        "beneficios": "Alta fixação ideal para ocasiões noturnas, com evolução floral sofisticada e longa permanência.",
        "restricoes": "Uso externo. Evitar contato com olhos e mucosas.",
    },
    "8V4C6N": {
        "publico_alvo": "Homens que valorizam conexão com a natureza e fragrâncias amadeiradas verdes.",
        "descricao": "Arbo Desodorante Colônia inspirado na floresta com notas de madeira, musgo e especiarias.",
        "como_usar": "Pulverizar após o banho em pulsos, pescoço e tórax.",
        "beneficios": "Fragrância envolvente com fixação equilibrada e perfil aromático natural.",
        "restricoes": "Não aplicar sobre pele lesionada. Manter fora do alcance de crianças.",
    },
    "9C4M1H": {
        "publico_alvo": "Cabelos ressecados que precisam de condicionamento nutritivo complementar.",
        "descricao": "Condicionador Match Nutrição Regeneradora com fórmula rica em ativos reparadores.",
        "como_usar": "Aplicar nos cabelos limpos e úmidos, do meio às pontas. Deixe agir 1-3 min e enxágue.",
        "beneficios": "Desembaraço imediato com nutrição profunda e proteção contra ressecamento.",
        "restricoes": "Evitar contato com olhos. Uso externo.",
    },
    "9H5W1T": {
        "publico_alvo": "Mulheres que apreciam perfumaria artesanal com inspiração botânica.",
        "descricao": "Botica 214 Peônia e Apricot Eau de Parfum com peônia, damasco e flores delicadas.",
        "como_usar": "Aplicar em pontos de pulsação para melhor evolução da fragrância.",
        "beneficios": "Perfil floral-frutado elegante com fixação equilibrada.",
        "restricoes": "Produto inflamável. Uso externo apenas.",
    },
    "9P3W7C": {
        "publico_alvo": "Pessoas que desejam pele hidratada com fragrância gourmand e acolhedora.",
        "descricao": "Loção hidratante Cuide-se Bem Deleite com notas de chocolate branco e avelã.",
        "como_usar": "Espalhar generosamente pelo corpo após o banho, massageando até absorver.",
        "beneficios": "Hidratação intensa com fórmula vegana e perfume adocicado de longa duração.",
        "restricoes": "Uso externo. Não aplicar sobre pele lesionada.",
    },
    "A8T3K5": {
        "publico_alvo": "Pessoas com cabelos cacheados que buscam definição e hidratação acessível.",
        "descricao": "Shampoo Cuide-se Bem Feira Cachos de Uva com extrato de uva e fórmula para cachos.",
        "como_usar": "Aplicar nos cabelos molhados, massagear e enxaguar. Ideal para uso diário.",
        "beneficios": "Define cachos com leveza, hidratação e perfume frutado agradável.",
        "restricoes": "Evitar contato com olhos. Uso externo.",
    },
    "B7F4L9": {
        "publico_alvo": "Pessoas com pele sensível que buscam hidratação suave e perfumada.",
        "descricao": "Loção Cuide-se Bem Rosa e Algodão com textura leve e fragrância floral delicada.",
        "como_usar": "Aplicar diariamente sobre pele limpa, especialmente após banho ou exposição ao sol.",
        "beneficios": "Fórmula hipoalergênica desenvolvida para pele sensível, com hidratação de 48 horas.",
        "restricoes": "Uso externo. Suspender uso em caso de reação alérgica.",
    },
    "D1W5N9": {
        "publico_alvo": "Mulheres que apreciam fragrâncias florais delicadas e femininas.",
        "descricao": "Lily Gardênia Eau de Parfum com destaque para gardênia, flores brancas e musk suave.",
        "como_usar": "Borrife sobre pele hidratada em regiões de pulsação para intensificar a fixação noturna.",
        "beneficios": "Fragrância floral envolvente com alta fixação perfeita para eventos e encontros noturnos.",
        "restricoes": "Produto inflamável. Não aplicar sobre pele irritada.",
    },
    "E4N8J1": {
        "publico_alvo": "Cabelos ressecados ou danificados que buscam nutrição com óleo de coco.",
        "descricao": "Shampoo Cuide-se Bem Feira Óleo de Coco com óleo de coco e fórmula nutritiva.",
        "como_usar": "Aplicar nos cabelos molhados, massagear e enxaguar abundantemente.",
        "beneficios": "Nutrição intensa com óleo de coco que devolve maciez e brilho aos fios.",
        "restricoes": "Evitar contato com olhos. Uso externo.",
    },
    "F3P9W2": {
        "publico_alvo": "Mulheres com cabelos cacheados ou ondulados que buscam definição e nutrição.",
        "descricao": "Shampoo Match Ciência das Curvas com tecnologia específica para cabelos com curvatura.",
        "como_usar": "Aplicar nos cabelos molhados, massagear o couro cabeludo e enxaguar. Repita se necessário.",
        "beneficios": "Limpeza equilibrada que preserva a forma dos cachos e reduz o frizz.",
        "restricoes": "Evitar contato com os olhos. Uso externo.",
    },
    "G7Q2D4": {
        "publico_alvo": "Mulheres que valorizam perfumaria sofisticada com perfil floral branco.",
        "descricao": "Elysée Blanc Eau de Parfum com acordes de flores brancas, almíscar e madeira clara.",
        "como_usar": "Borrife em pulsos, pescoço e decote após hidratação corporal.",
        "beneficios": "Elegância olfativa refinada com fixação prolongada e projeção moderada.",
        "restricoes": "Produto inflamável. Não aplicar em pele lesionada.",
    },
    "H3L9Q1": {
        "publico_alvo": "Homens dinâmicos que apreciam fragrâncias aquáticas e energizantes.",
        "descricao": "Quasar Deep Blue Desodorante Colônia com acordes marinhos, cítricos e amadeirados.",
        "como_usar": "Aplicar sobre pele limpa e seca, principalmente tórax e região cervical.",
        "beneficios": "Sensação refrescante imediata com fragrância masculina de longa duração.",
        "restricoes": "Evitar contato com olhos. Uso externo apenas.",
    },
    "H8Q3N1": {
        "publico_alvo": "Homens com caspa ou descamação no couro cabeludo que buscam limpeza profunda.",
        "descricao": "Shampoo esfoliante anticaspa Malbec com partículas esfoliantes e zinco piroitiona para combate à caspa.",
        "como_usar": "Aplicar no couro cabeludo molhado, massagear por 2 minutos enfatizando a esfoliação e enxaguar.",
        "beneficios": "Ação anticaspa com esfoliação do couro cabeludo, removendo descamação e oleosidade excessiva.",
        "restricoes": "Uso externo. Evitar contato com olhos. Não utilizar em couro cabeludo lesionado.",
    },
    "K8M2Q1": {
        "publico_alvo": "Pessoas que apreciam sabonete cremoso com fragrância frutada e envolvente.",
        "descricao": "Sabonete em barra Cuide-se Bem Cereja com fórmula cremosa e perfume de cereja doce.",
        "como_usar": "Espuma o sabonete nas mãos ou na esponja e aplique sobre pele molhada. Enxágue bem.",
        "beneficios": "Limpeza suave que respeita a barreira cutânea com fragrância duradoura.",
        "restricoes": "Uso externo. Em caso de irritação, suspenda o uso.",
    },
    "L6K1C8": {
        "publico_alvo": "Pessoas com cabelos oleosos ou mistos que precisam de controle de oleosidade.",
        "descricao": "Shampoo Match Oleosidade Controlada com agentes seborreguladores e limpeza profunda.",
        "como_usar": "Massagear nos cabelos molhados focando no couro cabeludo. Enxágue abundantemente.",
        "beneficios": "Reduz a oleosidade excessiva mantendo leveza e frescor por mais tempo.",
        "restricoes": "Uso externo. Evitar contato com olhos.",
    },
    "M9D3K7": {
        "publico_alvo": "Consumidores conscientes que utilizam refil para reduzir resíduos.",
        "descricao": "Refil de sabonete líquido Nativa SPA Orquídea Noire para reabastecer embalagem original.",
        "como_usar": "Despejar o refil na embalagem Nativa SPA Orquídea Noire e utilizar normalmente.",
        "beneficios": "Mesma fórmula cremosa e fragrância Orquídea Noire com embalagem sustentável.",
        "restricoes": "Uso externo. Manter refil fechado até o momento de uso.",
    },
    "N6A1V8": {
        "publico_alvo": "Mulheres que buscam fragrância sensual e misteriosa para ocasiões especiais.",
        "descricao": "Glamour Secrets Black Desodorante Colônia com notas orientais, florais e amadeiradas.",
        "como_usar": "Aplicar sobre pele limpa e seca em pontos de pulsação.",
        "beneficios": "Fragrância marcante e sedutora com boa duração.",
        "restricoes": "Uso externo. Manter ao abrigo de calor excessivo.",
    },
    "P1T8R5": {
        "publico_alvo": "Homens jovens que buscam fragrância adocicada, vibrante e sedutora.",
        "descricao": "Egeo Bomb Black Desodorante Colônia com notas gourmand, especiadas e amadeiradas.",
        "como_usar": "Aplicar sobre pele limpa em pontos de pulsação para melhor fixação.",
        "beneficios": "Fragrância marcante e jovem com boa projeção e personalidade intensa.",
        "restricoes": "Uso externo. Suspender uso em caso de irritação cutânea.",
    },
    "Q4H8L2": {
        "publico_alvo": "Homens que apreciam perfumaria premium com assinatura amadeirada e elegante.",
        "descricao": "Eau de Parfum Malbec 90ml com acordes de bergamota, lavanda, gerânio e base amadeirada.",
        "como_usar": "Borrife a 20 cm da pele em pontos de pulsação: pulsos, pescoço e atrás das orelhas.",
        "beneficios": "Alta concentração de essências para fixação superior e evolução olfativa sofisticada.",
        "restricoes": "Produto inflamável. Não aplicar sobre pele irritada ou lesionada.",
    },
    "R5B7Q3": {
        "publico_alvo": "Cabelos ressecados ou danificados que necessitam de nutrição profunda.",
        "descricao": "Shampoo Match Nutrição Regeneradora com ativos nutritivos para reconstrução capilar.",
        "como_usar": "Massagear nos cabelos molhados do comprimento às pontas. Enxágue bem.",
        "beneficios": "Nutrição intensa que devolve maciez, brilho e vitalidade aos fios danificados.",
        "restricoes": "Uso externo. Evitar contato com olhos.",
    },
    "T2N8H4": {
        "publico_alvo": "Pessoas que apreciam fragrâncias tropicais e hidratação diária.",
        "descricao": "Loção hidratante Cuide-se Bem Beijinho com perfume de coco e caramelo.",
        "como_usar": "Massagear sobre o corpo todo após o banho até completa absorção.",
        "beneficios": "Hidratação prolongada com textura não oleosa e fragrância envolvente.",
        "restricoes": "Uso externo. Evitar contato com olhos.",
    },
    "V2L9D6": {
        "publico_alvo": "Homens e mulheres com queda de cabelo ou afinamento capilar.",
        "descricao": "Shampoo antiqueda Malbec formulado para fortalecer os fios e reduzir a queda de cabelo.",
        "como_usar": "Massagear no couro cabeludo molhado por 2-3 minutos. Enxágue e repita se desejar.",
        "beneficios": "Fortalece a fibra capilar, combate a queda de cabelo e estimula a sensação de densidade.",
        "restricoes": "Uso externo. Evitar contato com olhos. Resultados variam conforme uso contínuo.",
    },
    "W9C5TD": {
        "publico_alvo": "Homens que desejam uma fragrância dourada e envolvente para ocasiões especiais.",
        "descricao": "Malbec Gold Desodorante Colônia com nuances ambaradas e acentos especiados intensos.",
        "como_usar": "Pulverizar sobre a pele limpa após o banho, evitando friccionar a área aplicada.",
        "beneficios": "Fragrância sofisticada com boa projeção e sensação de frescor duradouro.",
        "restricoes": "Não ingerir. Manter em local fresco, ao abrigo de luz solar direta.",
    },
    "X1Q8V3": {
        "publico_alvo": "Homens e mulheres fãs da fragrância Malbec que buscam higiene perfumada.",
        "descricao": "Sabonete em barra Malbec com essência amadeirada característica da linha.",
        "como_usar": "Espuma sobre pele molhada, massageie e enxágue completamente.",
        "beneficios": "Limpeza eficaz com perfume marcante da linha Malbec.",
        "restricoes": "Uso externo. Evitar contato com mucosas.",
    },
    "Y4C2L7": {
        "publico_alvo": "Mulheres que preferem fragrâncias frescas, florais e levemente cítricas.",
        "descricao": "Floratta Blue Desodorante Colônia com acordes aquáticos, florais e frutados.",
        "como_usar": "Pulverizar sobre pele seca em pontos estratégicos de fixação.",
        "beneficios": "Sensação de frescor duradouro com perfil feminino e elegante.",
        "restricoes": "Evitar contato com olhos. Suspender uso em caso de alergia.",
    },
    "Z5C1R8": {
        "publico_alvo": "Pessoas que buscam firmeza corporal com hidratação nutritiva.",
        "descricao": "Loção firmadora Nativa SPA Quinoa com quinoa, manteiga de karité e óleo de macadâmia.",
        "como_usar": "Aplicar com movimentos ascendentes sobre pele limpa, focando braços, coxas e abdômen.",
        "beneficios": "Ação firmadora com hidratação profunda e textura sedosa enriquecida com ativos naturais.",
        "restricoes": "Uso externo. Não ingerir. Manter fora do alcance de crianças.",
    },
}


def _slugify(name_sku: str) -> str:
    """Build a boticario.com.br-style path slug from the catalog product name."""
    normalized = unicodedata.normalize("NFKD", name_sku)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "produto"


def _product_url(name_sku: str) -> str:
    """Best-guess official product page URL from the catalog name."""
    return f"{BOTICARIO_BASE}/{_slugify(name_sku)}/"


def claims_records() -> list[dict[str, Any]]:
    """Return five claim rows per catalog SKU in stable field order."""
    catalog = {row["cod_sku"]: row for row in CATALOG}
    rows: list[dict[str, Any]] = []
    for row in CATALOG:
        sku = row["cod_sku"]
        claims = _CLAIMS_BY_SKU[sku]
        for claim_type in CLAIM_TYPES:
            rows.append(
                {
                    "cod_sku": sku,
                    "claim_type": claim_type,
                    "claim_text": claims[claim_type],
                }
            )
    assert len(rows) == len(CATALOG) * len(CLAIM_TYPES)
    assert set(_CLAIMS_BY_SKU) == set(catalog)
    return rows


def build_claims_manifest() -> list[dict[str, str]]:
    """Source metadata for ``claims_manifest.json`` (one row per SKU)."""
    return [
        {
            "cod_sku": row["cod_sku"],
            "source_url": _product_url(row["name_sku"]),
            "captured_at": CAPTURED_AT,
        }
        for row in CATALOG
    ]


def ensure_claims_manifest(path: Path | None = None) -> Path:
    """Write ``claims_manifest.json`` under app ``data/``."""
    target = path or (data_dir() / "claims_manifest.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_claims_manifest(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def claims_by_sku() -> dict[str, dict[str, str]]:
    """Map SKU code to claim_type -> claim_text."""
    return dict(_CLAIMS_BY_SKU)
