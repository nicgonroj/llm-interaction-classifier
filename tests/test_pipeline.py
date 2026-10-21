import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from classifier.evaluate import evaluate  # noqa: E402
from classifier.pipeline import route_case  # noqa: E402
from classifier.providers import BaselineProvider  # noqa: E402
from classifier.schema import SchemaError, validate  # noqa: E402


class FakeProvider:
    name = "fake"

    def __init__(self, output):
        self.output = output

    def classify(self, text):
        return self.output


class SchemaTests(unittest.TestCase):
    def test_valid_output(self):
        out = validate({"category": "otro", "confidence": 0.9, "rationale": "ok"})
        self.assertEqual(out["category"], "otro")

    def test_rejects_unknown_category_and_extra_fields(self):
        with self.assertRaises(SchemaError):
            validate({"category": "inventada", "confidence": 0.9, "rationale": "x"})
        with self.assertRaises(SchemaError):
            validate({"category": "otro", "confidence": 0.9, "rationale": "x", "extra": 1})

    def test_rejects_confidence_out_of_range(self):
        with self.assertRaises(SchemaError):
            validate({"category": "otro", "confidence": 1.5, "rationale": "x"})


class RoutingTests(unittest.TestCase):
    def test_adverse_event_always_goes_to_human(self):
        p = FakeProvider({"category": "evento_adverso", "confidence": 0.99, "rationale": "x"})
        self.assertEqual(route_case("1", "texto", p).route, "human_review")

    def test_low_confidence_goes_to_human(self):
        p = FakeProvider({"category": "otro", "confidence": 0.5, "rationale": "x"})
        self.assertEqual(route_case("1", "texto", p).route, "human_review")

    def test_invalid_output_falls_back_and_goes_to_human(self):
        d = route_case("1", "Pidió muestras", FakeProvider({"label": "?"}))
        self.assertEqual(d.route, "human_review")
        self.assertEqual(d.provider, "baseline")

    def test_confident_case_is_automated(self):
        p = FakeProvider({"category": "solicitud_muestra", "confidence": 0.9, "rationale": "x"})
        self.assertEqual(route_case("1", "texto", p).route, "auto")


class BaselineTests(unittest.TestCase):
    def test_detects_adverse_event(self):
        out = BaselineProvider().classify("El paciente tuvo náuseas y mareo con el fármaco")
        self.assertEqual(out["category"], "evento_adverso")

    def test_evaluation_counts_missed_adverse_events(self):
        p = FakeProvider({"category": "otro", "confidence": 0.95, "rationale": "x"})
        decisions = [route_case("a", "texto", p)]
        report = evaluate(decisions, {"a": "evento_adverso"})
        self.assertEqual(report["eventos_adversos_sin_revision"], 1)


if __name__ == "__main__":
    unittest.main()
