"""Evalua la calidad de la recuperacion contra un set de preguntas.

Requiere Qdrant y Ollama corriendo, y los documentos ya indexados.

Uso (desde backend/, con el venv):
    python -m evaluation.evaluate

Metricas:
- recall@k : en cuantas preguntas el chunk correcto aparece dentro del top-k.
- MRR      : media de 1/rango del primer acierto (premia que salga arriba).
"""

import json
import unicodedata
from pathlib import Path

from app.rag.retriever import Retriever

TOP_K = 10  # se recuperan hasta 10 para poder medir el rango


def _normalize(text: str) -> str:
    """Minusculas, sin acentos y sin espacios extra, para comparar de forma robusta."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(without_accents.split())


def _matches(content: str, expected: str) -> bool:
    return _normalize(expected) in _normalize(content)


def main() -> None:
    questions = json.loads(
        (Path(__file__).parent / "questions.json").read_text(encoding="utf-8")
    )
    retriever = Retriever()

    ranks: list[int | None] = []
    print(f"{'rango':>6}  pregunta")
    print("-" * 70)
    for item in questions:
        points = retriever.search(item["question"], TOP_K)
        rank: int | None = None
        for position, point in enumerate(points, start=1):
            if _matches(point.payload.get("content", ""), item["expect_contains"]):
                rank = position
                break
        ranks.append(rank)
        label = f"#{rank}" if rank else "MISS"
        print(f"{label:>6}  {item['question'][:60]}")

    total = len(ranks)
    found = [r for r in ranks if r is not None]
    print("-" * 70)
    for k in (1, 3, 5):
        recall = sum(1 for r in found if r <= k) / total
        print(f"recall@{k}: {recall:.2f}")
    mrr = sum(1 / r for r in found) / total if total else 0.0
    print(f"MRR     : {mrr:.3f}   (encontrados {len(found)}/{total})")


if __name__ == "__main__":
    main()
