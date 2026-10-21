"""Genera interacciones sintéticas etiquetadas (sin datos reales de ningún cliente).

Uso: python data/generate_synthetic.py --n 300 --seed 7
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

DRUGS = ["Cardiolex", "Neurozan", "Gastrivel", "Dermatina", "Pulmovent", "Osteafix"]
SPECIALTIES = ["cardióloga", "neurólogo", "gastroenteróloga", "dermatólogo", "neumóloga", "traumatólogo"]

TEMPLATES = {
    "consulta_producto": [
        "La Dra. {sp} preguntó por la dosis de {drug} en pacientes con insuficiencia renal.",
        "Consultó si hay interacción entre {drug} y anticoagulantes; pidió el estudio pivotal.",
        "Quiere conocer el mecanismo de acción de {drug} y su indicación en adultos mayores.",
        "Pidió evidencia reciente sobre {drug} frente al tratamiento estándar.",
    ],
    "solicitud_muestra": [
        "Solicitó muestras de {drug} para iniciar tratamiento en su consulta.",
        "Pidió dejar unidades de {drug} y material de apoyo para pacientes.",
        "Necesita más muestras de {drug}; se acabaron las de la visita anterior.",
    ],
    "evento_adverso": [
        "Un paciente presentó náuseas y mareo intenso tras iniciar {drug}.",
        "Reporta erupción cutánea en una paciente con {drug}; suspendió el tratamiento.",
        "Comentó una posible reacción alérgica a {drug}; el paciente fue hospitalizado.",
        "Mencionó un efecto secundario leve con {drug} que no estaba en el folleto.",
    ],
    "reclamo_calidad": [
        "El envase de {drug} llegó con el sellado roto en dos cajas del mismo lote.",
        "Encontraron partículas en un frasco de {drug}; pide revisar el lote.",
        "Las tabletas de {drug} tienen un color distinto al habitual.",
    ],
    "acceso_y_precio": [
        "Preguntó por la cobertura de {drug} en Fonasa e isapres.",
        "Consulta si {drug} entra en la próxima licitación del hospital y a qué precio.",
        "Quiere saber si existe convenio o descuento para pacientes con {drug}.",
    ],
    "otro": [
        "Visita de cortesía; agendamos una nueva reunión para el próximo mes.",
        "Comentó que asistirá al congreso de la especialidad en noviembre.",
        "Solo confirmó su nuevo horario de atención.",
    ],
}

# Casos difíciles: paráfrasis sin palabras clave obvias, mezclas y errores de tipeo.
# La etiqueta sigue la prioridad operacional: un posible evento adverso manda.
HARD_TEMPLATES = {
    "consulta_producto": [
        "¿Se puede usar {drug} en embarazadas? Le interesa el dato antes de recetar.",
        "Quedó con dudas de cada cuánto tomar {drug} si el paciente olvida una toma.",
    ],
    "solicitud_muestra": [
        "Le gustaría tener unas cajitas de {drug} para que los pacientes lo prueben.",
        "Pidio muestas de {drug} (sic) para la semana que viene.",
    ],
    "evento_adverso": [
        "Una paciente se sintió muy mal la semana después de empezar {drug} y terminó en urgencias.",
        "De pasada, mientras pedía muestras de {drug}, contó que un paciente tuvo mareos al día siguiente.",
        "El hijo de un paciente llamó porque su papá amaneció con la cara hinchada tras tomar {drug}.",
    ],
    "reclamo_calidad": [
        "Dice que las cajas de {drug} que recibió la farmacia del hospital venían aplastadas y húmedas.",
        "Un paciente devolvió {drug} porque el blíster estaba abierto.",
    ],
    "acceso_y_precio": [
        "Sus pacientes dejan {drug} porque les sale muy caro; quiere alternativas.",
        "Preguntó si el seguro complementario reembolsa {drug}.",
    ],
    "otro": [
        "Conversamos sobre el congreso; nada más que reportar.",
        "Me pidió el contacto de la gerencia médica para invitarla a un seminario.",
    ],
}
HARD_SHARE = 0.25

# Distribución sesgada, como en la operación real: pocos eventos adversos.
WEIGHTS = {"consulta_producto": 30, "solicitud_muestra": 25, "acceso_y_precio": 15,
           "otro": 15, "reclamo_calidad": 7, "evento_adverso": 8}


def generate(n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    cats = list(WEIGHTS)
    rows = []
    for i in range(n):
        cat = rng.choices(cats, weights=[WEIGHTS[c] for c in cats])[0]
        hard = rng.random() < HARD_SHARE
        pool = HARD_TEMPLATES[cat] if hard else TEMPLATES[cat]
        text = rng.choice(pool).format(drug=rng.choice(DRUGS), sp=rng.choice(SPECIALTIES))
        rows.append({"id": f"INT-{i + 1:04d}", "text": text, "label": cat,
                     "difficulty": "hard" if hard else "standard"})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=300)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", default=str(Path(__file__).with_name("interactions.jsonl")))
    args = parser.parse_args()
    rows = generate(args.n, args.seed)
    Path(args.out).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                              encoding="utf-8")
    print(f"{len(rows)} interacciones -> {args.out}")


if __name__ == "__main__":
    main()
