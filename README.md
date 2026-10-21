# llm-interaction-classifier

Clasificación de interacciones comerciales con LLMs, **salida validada por JSON Schema** y **revisión humana
por excepción**. Es una recreación, con datos 100 % sintéticos, de un sistema que diseñé y llevé a producción:
clasifica miles de interacciones al mes entre representantes de una farmacéutica y profesionales de la salud.
El cliente lo renueva cada año.

> Este repositorio no contiene código, datos ni nombres de ningún cliente. Los fármacos, las especialidades
> y los textos son inventados.

## El problema

Un equipo comercial registra en el CRM miles de notas libres al mes. Hay que saber de qué trata cada una
(consultas, muestras, acceso y precio) y, sobre todo, **no dejar pasar ningún posible evento adverso ni
reclamo de calidad**, que tienen obligación regulatoria de reporte. Revisarlas todas a mano no escala, y
automatizarlas todas sin control no es aceptable.

## La solución

```text
nota del CRM ──► proveedor (LLM o línea base) ──► validación JSON Schema ──► enrutamiento
                                                     │ inválida                ├─ auto: confianza ≥ umbral
                                                     └─► línea base + persona  └─ persona: riesgo regulatorio,
                                                                                  baja confianza o salida inválida
```

- **Contrato de salida** (`schema.py`): categoría cerrada, confianza entre 0 y 1 y justificación breve. Una
  salida que no cumple el contrato nunca entra a la operación.
- **Revisión humana por excepción** (`pipeline.py`): pasan a una persona los eventos adversos y los reclamos
  de calidad, siempre, aunque el modelo esté seguro; también los casos bajo el umbral de confianza y
  cualquier salida inválida.
- **Proveedores intercambiables** (`providers.py`): una línea base sin red ni claves, OpenAI con
  `response_format: json_schema` estricto o Anthropic. Sin dependencias externas: solo biblioteca estándar.
- **Evaluación automatizada** (`evaluate.py`): accuracy global y por categoría, tasa de automatización,
  accuracy de lo automatizado y la métrica que más importa: **eventos adversos que se escaparon de la
  revisión humana**.

## Resultados de la línea base

Set sintético de 300 interacciones (`python data/generate_synthetic.py --n 300 --seed 7`): un 75 % de casos
estándar y un 25 % difíciles (paráfrasis, faltas de ortografía y mezclas de temas).

| Métrica | Línea base (reglas) |
|---|---:|
| Accuracy global | 79,3 % |
| Accuracy en casos estándar / difíciles | 100 % / 26,2 % |
| Casos automatizados | 53 % |
| Accuracy de lo automatizado | 99,4 % |
| Eventos adversos sin revisión humana | **1** |

El evento adverso que se escapó resume por qué hace falta un modelo de lenguaje:

> «De pasada, mientras pedía muestras de Pulmovent, contó que un paciente tuvo mareos al día siguiente.»
> → la línea base lo clasificó como `solicitud_muestra` con confianza 0,83.

Las reglas cuentan palabras; un LLM entiende que la mención del paciente es lo que manda. Para comparar,
corre el mismo set con un proveedor LLM (abajo). No publico cifras del LLM que no se puedan reproducir aquí.

## Cómo usarlo

```bash
python data/generate_synthetic.py --n 300 --seed 7
PYTHONPATH=src python -m classifier --provider baseline

# con un LLM (opcional)
export OPENAI_API_KEY=...        # o ANTHROPIC_API_KEY=...
PYTHONPATH=src python -m classifier --provider openai --threshold 0.8

python -m unittest discover -s tests
```

Las decisiones quedan en `output/decisions.jsonl` con la categoría, la confianza, la ruta y el motivo.

## Qué llevé a producción en el caso real

- Ingesta desde el CRM, normalización y clasificación semántica con Azure OpenAI.
- Revisión humana solo por excepción y un tablero en Power BI para el área médica.
- Evaluaciones automatizadas por versión de prompt o modelo, con casos de regresión.

## Stack

Python 3.10+ (solo biblioteca estándar) · OpenAI / Anthropic (opcional) · JSON Schema · unittest

---

**Nicolás González Rojas** · Head of Data & BI · [LinkedIn](https://www.linkedin.com/in/nicolas-gonzalez-rojas)
