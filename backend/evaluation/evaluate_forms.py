"""Evalua que formato se ofrece para cada pregunta. Requiere Ollama.

Uso (desde backend/, con el venv):
    python -m evaluation.evaluate_forms

Dos escenarios por pregunta:
- todos los formatos cargados: debe ofrecer el correcto y ningun otro;
- sin el formato correcto: no debe ofrecer ninguno. Es el fallo peligroso, porque
  un formato parecido pero equivocado ("cancelar semestre" para "cancelar materia")
  manda al estudiante a llenar el tramite que no es.

Los formatos son descripciones de ejemplo de form_cases.json; con los reales
cargados, reemplazarlas por las suyas y volver a calibrar.
"""

import json
import time
from pathlib import Path
from types import SimpleNamespace

from app.rag.embedding_service import EmbeddingService
from app.rag.form_matcher import choose_by_similarity, confirm_with_llm
from app.rag.query_router import _cosine


def main() -> None:
    data = json.loads((Path(__file__).parent / "form_cases.json").read_text(encoding="utf-8"))
    embedder = EmbeddingService()
    forms = [SimpleNamespace(name=name, description=text) for name, text in data["forms"].items()]
    form_vectors = embedder.embed([form.description for form in forms])
    questions = [case["question"] for case in data["cases"]]
    question_vectors = embedder.embed(questions)

    for label, choose in (("embeddings", lambda q, s: choose_by_similarity(s)), ("llm", confirm_with_llm)):
        print(f"\n=== {label} ===")
        ok_all = ok_missing = total_missing = 0
        started = time.perf_counter()
        for case, vector in zip(data["cases"], question_vectors):
            scored = sorted(
                ((form, _cosine(vector, fv)) for form, fv in zip(forms, form_vectors)),
                key=lambda pair: pair[1],
                reverse=True,
            )
            expected = case["expected"]

            offered = [form.name for form, _ in choose(case["question"], scored)]
            hit = offered == ([expected] if expected else [])
            ok_all += hit
            mark = "OK " if hit else "MAL"
            line = f"{mark} {case['question'][:46]:46} -> {offered or '(ninguno)'}"

            if expected:
                total_missing += 1
                without = [pair for pair in scored if pair[0].name != expected]
                wrong = [form.name for form, _ in choose(case["question"], without)]
                ok_missing += not wrong
                if wrong:
                    line += f" | SIN EL CORRECTO ofrece {wrong}"
            print(line)

        n = len(data["cases"])
        print("-" * 70)
        print(f"con todos los formatos: {ok_all}/{n} exactos")
        print(f"sin el formato correcto: {ok_missing}/{total_missing} no ofrecen uno equivocado")
        print(f"tiempo: {(time.perf_counter() - started) / n * 1000:.0f} ms por pregunta (dos escenarios)")


if __name__ == "__main__":
    main()
