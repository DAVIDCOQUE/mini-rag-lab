"""Mide de punta a punta que preguntas responde Sara con el corpus actual, y cuanto tarda.

Requiere Ollama, Qdrant y los documentos indexados.

Uso (desde backend/, con el venv):
    python -m evaluation.evaluate_coverage                    # ambos routers
    python -m evaluation.evaluate_coverage --mode embedding
    python -m evaluation.evaluate_coverage --out reporte.md

Cada pregunta va suelta (sin historial), como en /search. Veredictos:
- ok: covered con alguna palabra esperada y el formato correcto si aplica; missing que
  dice no saber; las demas categorias, cuando el router elige su camino.
- no_sabe: covered que respondio la frase de no-respuesta (falla de recuperacion).
- incompleta: covered que respondio sin ninguna palabra esperada (revisar a mano).
- sin_formato: respuesta correcta pero no ofrecio el formato esperado.
- invento: missing que respondio algo en vez de decir que no sabe.
- mal_ruteo: general, smalltalk u off_topic que fue por otro camino.
"""

import argparse
import json
import statistics
import time
import unicodedata
from collections import Counter
from pathlib import Path

from app.core.config import settings
from app.database.session import SessionLocal
from app.rag.prompt_builder import says_no_answer
from app.services import rag_service

CASES = Path(__file__).with_name("coverage_cases.json")


def _plain(text: str) -> str:
    """Minusculas y sin tildes: la comparacion no depende de como escriba el modelo."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _verdict(case: dict, answer: str, route: str, forms: list[str]) -> str:
    category = case["category"]
    said_no = says_no_answer(answer)
    if category == "covered":
        if said_no:
            return "no_sabe"
        if not any(_plain(word) in _plain(answer) for word in case["any"]):
            return "incompleta"
        expected = case.get("form")
        if expected and expected not in forms:
            return "sin_formato"
        return "ok"
    if category == "missing":
        return "ok" if said_no else "invento"
    return "ok" if route == category else "mal_ruteo"


def _offered_codes(outcome) -> list[str]:
    """Codigos entregados (outcome.forms) u ofrecidos en el texto de la respuesta."""
    codes = {form.form_code for form, _ in outcome.forms if form.form_code}
    text = outcome.answer.upper()
    for code in ("R-GA001", "R-GA002", "R-GA003", "R-GA004", "R-GA005"):
        if f"FORMATO {code}" in text or f"{code} (" in text:
            codes.add(code)
    return sorted(codes)


def evaluate(mode: str, cases: list[dict]) -> list[dict]:
    # El router y la confirmacion de formatos leen el modo de settings.
    settings.ROUTER_MODE = mode
    rows = []
    print(f"\n=== router: {mode} ===")
    with SessionLocal() as db:
        for case in cases:
            started = time.perf_counter()
            outcome = rag_service.answer_question(db, case["message"])
            total_ms = (time.perf_counter() - started) * 1000
            forms = _offered_codes(outcome)
            verdict = _verdict(case, outcome.answer, outcome.route.value, forms)
            rows.append(
                {
                    "mode": mode,
                    **case,
                    "route": outcome.route.value,
                    "router": outcome.router,
                    "verdict": verdict,
                    "forms": forms,
                    "top_score": round(outcome.points[0].score, 2) if outcome.points else None,
                    "routing_ms": outcome.routing_ms,
                    "retrieval_ms": outcome.retrieval_ms,
                    "generation_ms": outcome.generation_ms,
                    "total_ms": round(total_ms, 1),
                    "answer": outcome.answer,
                }
            )
            mark = "  " if verdict == "ok" else "XX"
            print(f"{mark} {verdict:<11} {total_ms / 1000:5.1f}s  [{outcome.route.value}] {case['message']}")
    _summary(rows)
    return rows


def _ms(values: list[float | None]) -> str:
    present = [v for v in values if v is not None]
    if not present:
        return "-"
    return f"{statistics.median(present) / 1000:.1f}s (max {max(present) / 1000:.1f}s)"


def _summary(rows: list[dict]) -> None:
    by_category: dict[str, Counter] = {}
    for row in rows:
        by_category.setdefault(row["category"], Counter())[row["verdict"]] += 1
    for category, counts in by_category.items():
        total = sum(counts.values())
        detail = ", ".join(f"{k}={v}" for k, v in counts.most_common() if k != "ok")
        print(f"  {category:<10} {counts['ok']}/{total} ok  {detail}")
    print(
        f"  tiempos (mediana): total {_ms([r['total_ms'] for r in rows])}, "
        f"router {_ms([r['routing_ms'] for r in rows])}, "
        f"recuperacion {_ms([r['retrieval_ms'] for r in rows])}, "
        f"generacion {_ms([r['generation_ms'] for r in rows])}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["llm", "embedding"])
    parser.add_argument("--out", help="Guarda todas las filas en JSON para revisarlas a mano.")
    args = parser.parse_args()

    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    rag_service.warm_up()
    rows = []
    for mode in [args.mode] if args.mode else ["llm", "embedding"]:
        rows += evaluate(mode, cases)
    if args.out:
        Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
