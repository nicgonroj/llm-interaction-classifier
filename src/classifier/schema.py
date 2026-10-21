"""Contrato de salida del clasificador.

Toda respuesta, venga de un LLM o del modelo base, debe cumplir este esquema
antes de entrar a la operación. Si no lo cumple, el caso va a revisión humana.
"""
from __future__ import annotations

CATEGORIES = (
    "consulta_producto",
    "solicitud_muestra",
    "evento_adverso",
    "reclamo_calidad",
    "acceso_y_precio",
    "otro",
)

# Categorías que, por riesgo regulatorio, siempre pasan por una persona.
ALWAYS_REVIEW = frozenset({"evento_adverso", "reclamo_calidad"})

OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["category", "confidence", "rationale"],
    "properties": {
        "category": {"type": "string", "enum": list(CATEGORIES)},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "rationale": {"type": "string", "minLength": 1, "maxLength": 300},
    },
}


class SchemaError(ValueError):
    """La salida no cumple el contrato."""


def validate(output: object) -> dict:
    """Valida la salida contra OUTPUT_SCHEMA sin dependencias externas."""
    if not isinstance(output, dict):
        raise SchemaError("la salida no es un objeto JSON")
    props = OUTPUT_SCHEMA["properties"]
    extra = set(output) - set(props)
    if extra:
        raise SchemaError(f"campos no permitidos: {sorted(extra)}")
    missing = [k for k in OUTPUT_SCHEMA["required"] if k not in output]
    if missing:
        raise SchemaError(f"faltan campos: {missing}")
    if output["category"] not in CATEGORIES:
        raise SchemaError(f"categoría desconocida: {output['category']!r}")
    conf = output["confidence"]
    if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
        raise SchemaError(f"confianza fuera de rango: {conf!r}")
    rationale = output["rationale"]
    if not isinstance(rationale, str) or not 1 <= len(rationale) <= 300:
        raise SchemaError("la justificación debe tener entre 1 y 300 caracteres")
    return {"category": output["category"], "confidence": float(conf), "rationale": rationale}
