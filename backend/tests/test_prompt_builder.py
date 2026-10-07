from app.rag import prompt_builder
from app.schemas.chat import ChatTurn


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
    instrucciones = prompt_builder.institutional_instructions()

    assert prompt_builder.NO_ANSWER_PLACEHOLDER not in instrucciones
    assert prompt_builder.NO_ANSWER_MESSAGE in instrucciones


def test_el_mensaje_con_contexto_incluye_todos_los_chunks_y_la_pregunta():
    mensaje = prompt_builder.build_context_message(
        "¿Cuanto se destina?", ["El 2% del presupuesto.", "Segundo fragmento."]
    )

    assert "El 2% del presupuesto." in mensaje
    assert "Segundo fragmento." in mensaje
    assert "Pregunta: ¿Cuanto se destina?" in mensaje


def test_el_recordatorio_de_no_revelar_el_contexto_va_al_final():
    mensaje = prompt_builder.build_context_message("¿Y?", ["dato"])

    assert mensaje.endswith(prompt_builder.CONTEXT_REMINDER)


def test_una_variante_reemplaza_las_instrucciones_del_repositorio():
    instrucciones = prompt_builder.institutional_instructions("Instrucciones propias.")

    assert instrucciones == "Instrucciones propias."


def test_los_mensajes_van_sistema_historial_y_pregunta_actual():
    historial = [{"role": "user", "content": "hola"}, {"role": "assistant", "content": "hola, David"}]

    mensajes = prompt_builder.build_messages("sistema", "¿y la matricula?", historial)

    assert [m["role"] for m in mensajes] == ["system", "user", "assistant", "user"]
    assert mensajes[-1]["content"] == "¿y la matricula?"


def _turnos(*pares: tuple[str, str]) -> list[ChatTurn]:
    return [ChatTurn(role=rol, content=texto) for rol, texto in pares]


def test_el_historial_que_cabe_viaja_completo():
    historial = _turnos(("user", "soy David"), ("assistant", "hola David"), ("user", "¿y la matricula?"))

    turnos = prompt_builder.fit_history(historial, max_tokens=1000, answer_chars=600)

    assert [t["content"] for t in turnos] == ["soy David", "hola David", "¿y la matricula?"]


def test_al_recortar_se_conserva_el_primer_mensaje_y_los_mas_recientes():
    historial = _turnos(
        ("user", "Hola, soy David, de ingenieria"),
        ("assistant", "a" * 400),
        ("user", "b" * 400),
        ("assistant", "c" * 400),
        ("user", "¿y cuanto cuesta?"),
        ("assistant", "Cuesta poco."),
    )

    # Cabe el primer mensaje mas unos 120 tokens: solo los dos ultimos turnos.
    turnos = prompt_builder.fit_history(historial, max_tokens=130, answer_chars=600)

    assert turnos[0]["content"] == "Hola, soy David, de ingenieria"
    assert [t["content"] for t in turnos[1:]] == ["¿y cuanto cuesta?", "Cuesta poco."]


def test_el_tramo_recortado_no_empieza_por_una_respuesta_huerfana():
    historial = _turnos(
        ("user", "soy David"),
        ("assistant", "x" * 40),
        ("user", "y" * 400),
        ("assistant", "respuesta corta"),
    )

    # Cabe la respuesta final pero no la pregunta que la origino.
    turnos = prompt_builder.fit_history(historial, max_tokens=20, answer_chars=600)

    assert [t["content"] for t in turnos] == ["soy David"]


def test_las_respuestas_previas_se_recortan_y_las_preguntas_no():
    historial = _turnos(("user", "p" * 900), ("assistant", "r" * 900))

    turnos = prompt_builder.fit_history(historial, max_tokens=5000, answer_chars=600)

    assert len(turnos[0]["content"]) == 900
    assert turnos[1]["content"] == "r" * 600 + "…"


def test_sin_historial_no_hay_instruccion_de_turno():
    assert prompt_builder.with_turn_instruction("sistema", None) == "sistema"


def test_el_primer_turno_pide_saludar_y_los_siguientes_no():
    primero = prompt_builder.with_turn_instruction("sistema", [])
    siguiente = prompt_builder.with_turn_instruction("sistema", _turnos(("user", "hola")))

    assert primero.endswith(prompt_builder.FIRST_TURN_INSTRUCTION)
    assert siguiente.endswith(prompt_builder.FOLLOW_UP_INSTRUCTION)


def test_sin_saludo_del_modelo_el_primer_turno_pide_no_saludar():
    sistema = prompt_builder.with_turn_instruction("sistema", [], llm_greets=False)

    assert sistema.endswith(prompt_builder.NO_GREETING_INSTRUCTION)
