"""Evalua el router contra casos etiquetados, incluidos seguimientos con historial.

Requiere Ollama corriendo (no Qdrant ni documentos indexados).

Uso (desde backend/, con el venv):
    python -m evaluation.evaluate_routing                  # ambos routers
    python -m evaluation.evaluate_routing --mode embedding
    python -m evaluation.evaluate_routing --cases routing_holdout.json

routing_cases.json es para iterar; routing_holdout.json esta reservado para medir si
una mejora generaliza, asi que no se ajustan ejemplos ni prompts mirandolo.

Mide si se elige el camino correcto, no la calidad de la pregunta de busqueda: un
seguimiento puede acertar el camino y aun asi buscar sin el tema de la conversacion.
Por eso se imprime la pregunta con la que buscaria cada caso institucional.
"""

import argparse
import json
import time
from collections import Counter
from pathlib import Path

from app.schemas.chat import ChatTurn
from app.services import rag_service


def evaluate(mode: str, cases: list[dict], histories: dict[str, list[ChatTurn]]) -> None:
    hits: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    fallbacks = 0
    elapsed = 0.0

    print(f"\n=== router: {mode} ===")
    for case in cases:
        history = histories.get(case["history"]) if "history" in case else None
        started = time.perf_counter()
        decision = rag_service.route_query(case["message"], history, mode=mode)
        elapsed += time.perf_counter() - started

        if decision.router != mode:
            fallbacks += 1
        expected = case["expected"]
        totals[expected] += 1
        ok = decision.route.value == expected
        hits[expected] += ok

        mark = "OK " if ok else "MAL"
        tag = f"[{case['history']}]" if history else ""
        line = f"{mark} {case['message'][:42]:42} {tag:15} -> {decision.route.value:13}"
        if not ok:
            line += f" (esperado {expected})"
        elif decision.route.value == "institutional" and decision.search_query != case["message"]:
            line += f" busca: {decision.search_query[:60]}"
        print(line)

    total = sum(totals.values())
    print("-" * 70)
    print(f"aciertos: {sum(hits.values())}/{total} = {sum(hits.values()) / total:.0%}")
    for route in totals:
        print(f"  {route:13} {hits[route]}/{totals[route]}")
    print(f"tiempo medio: {elapsed / total * 1000:.0f} ms por mensaje")
    if fallbacks:
        print(f"AVISO: {fallbacks} casos cayeron al router de respaldo")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["llm", "embedding", "both"], default="both")
    parser.add_argument("--cases", default="routing_cases.json")
    args = parser.parse_args()

    data = json.loads((Path(__file__).parent / args.cases).read_text(encoding="utf-8"))
    histories = {
        name: [ChatTurn(**turn) for turn in turns] for name, turns in data["histories"].items()
    }
    modes = ["embedding", "llm"] if args.mode == "both" else [args.mode]
    for mode in modes:
        evaluate(mode, data["cases"], histories)


if __name__ == "__main__":
    main()
