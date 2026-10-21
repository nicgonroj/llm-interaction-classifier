"""Proveedores de clasificación.

- ``BaselineProvider``: reglas ponderadas, sin red ni claves. Sirve como línea
  base reproducible y como respaldo si el LLM no responde.
- ``OpenAIProvider`` y ``AnthropicProvider``: piden salida JSON estructurada.
  Solo se usan si existe la variable de entorno con la clave.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
import urllib.request

from .schema import CATEGORIES, OUTPUT_SCHEMA

SYSTEM_PROMPT = (
    "Clasificas interacciones comerciales entre representantes de una compañía "
    "farmacéutica y profesionales de la salud. Responde solo con un objeto JSON "
    "que cumpla el esquema entregado. Usa 'evento_adverso' ante cualquier mención "
    "de un efecto no deseado en un paciente, aunque sea leve o dudosa. Si no estás "
    "seguro, baja la confianza en vez de adivinar."
)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


class BaselineProvider:
    name = "baseline"

    KEYWORDS = {
        "evento_adverso": ["reaccion", "efecto adverso", "efecto secundario", "nauseas", "mareo",
                           "erupcion", "hospitaliz", "suspendio el tratamiento", "alergia"],
        "reclamo_calidad": ["lote", "envase", "sellado", "particulas", "vencid", "dañad",
                            "danad", "color distinto", "mal estado"],
        "solicitud_muestra": ["muestra", "muestras", "material de apoyo", "folleto", "dejar unidades"],
        "acceso_y_precio": ["precio", "isapre", "fonasa", "cobertura", "licitacion", "convenio",
                            "descuento", "arancel"],
        "consulta_producto": ["dosis", "posologia", "interaccion", "contraindic", "estudio",
                              "evidencia", "mecanismo", "indicacion"],
    }

    def classify(self, text: str) -> dict:
        norm = _normalize(text)
        scores = {
            cat: sum(1 for kw in kws if kw in norm) for cat, kws in self.KEYWORDS.items()
        }
        best = max(scores, key=scores.get)
        total = sum(scores.values())
        if total == 0:
            return {"category": "otro", "confidence": 0.4,
                    "rationale": "Sin señales claras de ninguna categoría."}
        confidence = round(0.5 + 0.5 * scores[best] / total, 2)
        hits = [kw for kw in self.KEYWORDS[best] if kw in norm][:3]
        return {"category": best, "confidence": confidence,
                "rationale": f"Señales detectadas: {', '.join(hits)}."}


def _post_json(url: str, headers: dict, payload: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _extract_json(text: str) -> object:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("la respuesta no contiene JSON")
    return json.loads(match.group(0))


class OpenAIProvider:
    name = "openai"

    def __init__(self, model: str | None = None):
        self.api_key = os.environ["OPENAI_API_KEY"]
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def classify(self, text: str) -> object:
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": text}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "interaction_label", "strict": True, "schema": OUTPUT_SCHEMA}},
        }
        data = _post_json("https://api.openai.com/v1/chat/completions",
                          {"Authorization": f"Bearer {self.api_key}"}, payload)
        return json.loads(data["choices"][0]["message"]["content"])


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, model: str | None = None):
        self.api_key = os.environ["ANTHROPIC_API_KEY"]
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")

    def classify(self, text: str) -> object:
        prompt = (f"Esquema JSON:\n{json.dumps(OUTPUT_SCHEMA, ensure_ascii=False)}\n\n"
                  f"Categorías válidas: {', '.join(CATEGORIES)}\n\nInteracción:\n{text}")
        payload = {"model": self.model, "max_tokens": 300, "temperature": 0,
                   "system": SYSTEM_PROMPT,
                   "messages": [{"role": "user", "content": prompt}]}
        data = _post_json("https://api.anthropic.com/v1/messages",
                          {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}, payload)
        return _extract_json(data["content"][0]["text"])


def get_provider(name: str):
    providers = {"baseline": BaselineProvider, "openai": OpenAIProvider,
                 "anthropic": AnthropicProvider}
    if name not in providers:
        raise ValueError(f"proveedor desconocido: {name}")
    return providers[name]()
