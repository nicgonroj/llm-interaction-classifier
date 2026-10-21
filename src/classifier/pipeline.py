"""Clasifica, valida y enruta: automático o revisión humana por excepción."""
from __future__ import annotations

from dataclasses import dataclass

from .providers import BaselineProvider
from .schema import ALWAYS_REVIEW, SchemaError, validate


@dataclass
class Decision:
    id: str
    category: str
    confidence: float
    rationale: str
    route: str          # "auto" | "human_review"
    reason: str         # por qué se enrutó así
    provider: str


def route_case(case_id: str, text: str, provider, threshold: float = 0.75,
               fallback=None) -> Decision:
    fallback = fallback or BaselineProvider()
    used = provider.name
    try:
        label = validate(provider.classify(text))
    except (SchemaError, ValueError, KeyError, OSError) as exc:
        # Salida inválida o falla del proveedor: se usa la línea base y una persona revisa.
        label = validate(fallback.classify(text))
        return Decision(case_id, label["category"], label["confidence"], label["rationale"],
                        "human_review", f"salida inválida de {used}: {exc}", fallback.name)

    if label["category"] in ALWAYS_REVIEW:
        route, reason = "human_review", "categoría de riesgo regulatorio"
    elif label["confidence"] < threshold:
        route, reason = "human_review", f"confianza {label['confidence']:.2f} < {threshold:.2f}"
    else:
        route, reason = "auto", "confianza suficiente"
    return Decision(case_id, label["category"], label["confidence"], label["rationale"],
                    route, reason, used)
