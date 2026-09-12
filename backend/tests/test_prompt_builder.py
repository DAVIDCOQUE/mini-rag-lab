from app.rag import prompt_builder


def test_render_sustituye_el_marcador_por_la_frase_real():
    cuerpo = "Si no encuentras la respuesta di: {no_answer}"

    resultado = prompt_builder.render_system_prompt(cuerpo)

    assert resultado == f"Si no encuentras la respuesta di: {prompt_builder.NO_ANSWER_MESSAGE}"


def test_render_no_revienta_con_otras_llaves_del_usuario():
    # Por esto se usa replace y no format: una variante escrita desde la UI puede
    # traer llaves sueltas y no deberia tumbar la construccion del prompt.
    cuerpo = "Responde en {json} y usa {no_answer} si no sabes."

    resultado = prompt_builder.render_system_prompt(cuerpo)

    assert "{json}" in resultado
    assert prompt_builder.NO_ANSWER_MESSAGE in resultado


def test_el_prompt_del_repositorio_no_deja_el_marcador_sin_sustituir():
    prompt = prompt_builder.build_prompt("¿Quien firma?", ["Firma el secretario general."])

    assert prompt_builder.NO_ANSWER_PLACEHOLDER not in prompt
    assert prompt_builder.NO_ANSWER_MESSAGE in prompt


def test_build_prompt_incluye_todos_los_chunks_y_la_pregunta():
    prompt = prompt_builder.build_prompt(
        "¿Cuanto se destina?", ["El 2% del presupuesto.", "Segundo fragmento."]
    )

    assert "El 2% del presupuesto." in prompt
    assert "Segundo fragmento." in prompt
    assert "¿Cuanto se destina?" in prompt


def test_una_variante_reemplaza_las_instrucciones_del_repositorio():
    prompt = prompt_builder.build_prompt("¿Y?", ["dato"], system_prompt="Instrucciones propias.")

    assert prompt.startswith("Instrucciones propias.")
    assert "Reglas estrictas" not in prompt


def test_el_prompt_sin_contexto_no_lleva_seccion_de_contexto():
    prompt = prompt_builder.build_simple_prompt("hola", prompt_builder.SMALLTALK_PROMPT)

    assert "Contexto:" not in prompt
    assert "hola" in prompt
