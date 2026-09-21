from datetime import date

from bot import calcular_proximo_aniversario


def test_calcular_proximo_aniversario_antes_da_data():
    hoje = date(2026, 9, 21)
    nascimento = date(1995, 12, 5)

    assert calcular_proximo_aniversario(nascimento, hoje) == date(2026, 12, 5)


def test_calcular_proximo_aniversario_ja_passou_no_ano():
    hoje = date(2026, 12, 6)
    nascimento = date(1995, 12, 5)

    assert calcular_proximo_aniversario(nascimento, hoje) == date(2027, 12, 5)
