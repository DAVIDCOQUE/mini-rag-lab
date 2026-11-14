from types import SimpleNamespace

from app.rag import prompt_builder as pb


def _perfil(**datos):
    base = dict(
        assistant_name="Sara", assistant_gender="FEMININE", institution_name=None,
        institution_short_name=None, city=None, website=None, help_office=None,
        help_location=None, help_hours=None, help_phone=None, help_email=None,
    )
    return SimpleNamespace(**{**base, **datos})


def test_se_presenta_con_su_nombre_y_la_institucion():
    perfil = _perfil(institution_name="Universidad Santiago de Cali")

    assert pb.greeting(perfil) == "¡Hola! Soy Sara, la asistente académica de la Universidad Santiago de Cali."


def test_sin_institucion_se_presenta_de_la_universidad_en_masculino_si_toca():
    perfil = _perfil(assistant_name="Leo", assistant_gender="MASCULINE")

    assert pb.greeting(perfil) == "¡Hola! Soy Leo, el asistente académico de la universidad."


def test_sabe_que_si_lo_llaman_por_su_nombre_no_es_el_del_estudiante():
    assert "te esta hablando a ti" in pb.identity_instructions(_perfil())


def test_sin_datos_de_atencion_no_remite_a_ningun_lado():
    assert pb.help_sentence(_perfil()) is None


def test_remite_solo_con_los_datos_que_existen():
    perfil = _perfil(help_office="la Secretaría Académica", help_hours="lunes a viernes de 8 a 6", help_phone="518 3000")

    assert pb.help_sentence(perfil) == (
        "Puedes consultarlo en la Secretaría Académica, lunes a viernes de 8 a 6 o comunicarte al 518 3000."
    )




def test_contrae_de_el_en_del():
    perfil = _perfil(assistant_name="Leo", assistant_gender="MASCULINE", institution_name="Instituto Técnico")

    assert pb.greeting(perfil) == "¡Hola! Soy Leo, el asistente académico del Instituto Técnico."


import pytest


@pytest.mark.parametrize("mensaje", ["¿Cómo te llamas?", "¿Cuál es tu nombre?", "¿Quién eres?", "como te dicen"])
def test_reconoce_la_pregunta_por_su_nombre(mensaje):
    assert pb.asks_assistant_name(mensaje)


def test_no_confunde_otras_preguntas_con_la_de_su_nombre():
    assert not pb.asks_assistant_name("¿Quién es el rector?")
    assert not pb.asks_assistant_name("Hola Sara")


def test_dice_su_nombre_del_perfil():
    assert pb.name_message(_perfil(assistant_name="Sara")).startswith("Me llamo Sara, soy la asistente")
