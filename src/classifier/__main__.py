"""CLI: python -m classifier --provider baseline --data data/interactions.jsonl"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .evaluate import evaluate
from .pipeline import route_case
from .providers import get_provider


def main() -> None:
    parser = argparse.ArgumentParser(description="Clasificador de interacciones con revisión humana")
    parser.add_argument("--provider", default="baseline", choices=["baseline", "openai", "anthropic"])
    parser.add_argument("--data", default="data/interactions.jsonl")
    parser.add_argument("--threshold", type=float, default=0.75)
    parser.add_argument("--out", default="output/decisions.jsonl")
    args = parser.parse_args()

    rows = [json.loads(line) for line in Path(args.data).read_text(encoding="utf-8").splitlines() if line]
    provider = get_provider(args.provider)
    decisions = [route_case(r["id"], r["text"], provider, args.threshold) for r in rows]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(asdict(d), ensure_ascii=False) for d in decisions) + "\n",
                   encoding="utf-8")

    report = evaluate(decisions, {r["id"]: r["label"] for r in rows})
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
