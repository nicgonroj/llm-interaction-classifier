"""Métricas de calidad y de operación sobre un set etiquetado."""
from __future__ import annotations

from collections import Counter

from .schema import CATEGORIES


def evaluate(decisions, gold: dict) -> dict:
    """``gold`` mapea id -> categoría correcta."""
    n = len(decisions)
    correct = sum(d.category == gold[d.id] for d in decisions)
    auto = [d for d in decisions if d.route == "auto"]
    auto_correct = sum(d.category == gold[d.id] for d in auto)
    # Un evento adverso que se escapa del flujo humano es el error más caro.
    missed_ae = sum(1 for d in decisions
                    if gold[d.id] == "evento_adverso" and d.route == "auto")

    per_class = {}
    for cat in CATEGORIES:
        tp = sum(d.category == cat and gold[d.id] == cat for d in decisions)
        fp = sum(d.category == cat and gold[d.id] != cat for d in decisions)
        fn = sum(d.category != cat and gold[d.id] == cat for d in decisions)
        support = tp + fn
        if support == 0 and fp == 0:
            continue
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / support if support else 0.0
        per_class[cat] = {"precision": round(precision, 3), "recall": round(recall, 3),
                          "support": support}

    return {
        "casos": n,
        "accuracy": round(correct / n, 3) if n else 0.0,
        "tasa_automatizacion": round(len(auto) / n, 3) if n else 0.0,
        "accuracy_en_automaticos": round(auto_correct / len(auto), 3) if auto else None,
        "eventos_adversos_sin_revision": missed_ae,
        "motivos_revision": dict(Counter(d.reason.split(":")[0] for d in decisions
                                         if d.route == "human_review")),
        "por_categoria": per_class,
    }
