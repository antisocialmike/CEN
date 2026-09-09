import pytest
from server.src.controllers.payroll_controller import (
    IMSSStrategy,
    ISRStrategy,
    PayrollService,
    UMA_DIARIA,
)


def test_isr_calculation():
    strategy = ISRStrategy()
    assert strategy.calculate(10000) == 192.8


def test_isr_calculation_bajo_limite_de_subsidio():
    strategy = ISRStrategy()
    assert strategy.calculate(5000) == 0.0


def test_imss_calculation():
    strategy = IMSSStrategy()
    assert strategy.calculate(10000) == 237.5


def test_imss_calculation_con_excedente_de_3_uma():
    strategy = IMSSStrategy()
    assert strategy.calculate(20000) == 512.21


def test_process_salary_success():
    service = PayrollService()
    result = service.process_salary(10000)

    assert result["gross_salary"] == 10000.0
    assert result["isr_deduction"] == 192.8
    assert result["imss_deduction"] == 237.5
    assert result["net_salary"] == 9569.7


def test_process_salary_negative_value_raises_error():
    service = PayrollService()
    with pytest.raises(ValueError, match="El salario no puede ser negativo"):
        service.process_salary(-500)


def _items_by_concept(result):
    return {item["concept"]: item for item in result["items"]}


def test_una_nomina_sin_conceptos_extra_solo_lleva_sueldo_isr_e_imss():
    result = PayrollService().process({"gross_salary": 10000})

    assert list(_items_by_concept(result)) == ["sueldo", "isr", "imss"]
    assert result["total_perceptions"] == 10000
    assert result["net_salary"] == 9569.7


def test_horas_extra_dobles_y_triples_segun_la_ley_federal_del_trabajo():
    result = PayrollService().process({
        "gross_salary": 21000,
        "overtime_double_hours": 9,
        "overtime_triple_hours": 3
    })

    horas = _items_by_concept(result)["horas_extra"]
    assert horas["amount"] == 2362.5
    assert horas["taxable"] + horas["exempt"] == horas["amount"]


def test_la_mitad_de_las_horas_extra_esta_exenta():
    result = PayrollService().process({
        "gross_salary": 21000,
        "overtime_double_hours": 4
    })

    horas = _items_by_concept(result)["horas_extra"]
    assert horas["exempt"] == round(horas["amount"] * 0.5, 2)


def test_el_aguinaldo_sale_de_los_dias_de_salario_diario():
    result = PayrollService().process({
        "gross_salary": 21000,
        "christmas_bonus_days": 15
    })

    aguinaldo = _items_by_concept(result)["aguinaldo"]
    assert aguinaldo["amount"] == 10500.0
    assert aguinaldo["exempt"] == round(UMA_DIARIA * 30, 2)


def test_el_aguinaldo_pequeno_queda_totalmente_exento():
    result = PayrollService().process({
        "gross_salary": 6000,
        "christmas_bonus_days": 15
    })

    aguinaldo = _items_by_concept(result)["aguinaldo"]
    assert aguinaldo["amount"] == 3000.0
    assert aguinaldo["taxable"] == 0.0
    assert aguinaldo["exempt"] == 3000.0


def test_la_prima_vacacional_es_el_veinticinco_por_ciento():
    result = PayrollService().process({
        "gross_salary": 21000,
        "vacation_days": 12
    })

    prima = _items_by_concept(result)["prima_vacacional"]
    assert prima["amount"] == 2100.0
    assert prima["exempt"] == round(UMA_DIARIA * 15, 2)


def test_las_deducciones_adicionales_se_restan_del_neto():
    sin_deducciones = PayrollService().process({"gross_salary": 21000})
    con_deducciones = PayrollService().process({
        "gross_salary": 21000,
        "loan_deduction": 800,
        "housing_credit_deduction": 1200
    })

    assert con_deducciones["net_salary"] == round(
        sin_deducciones["net_salary"] - 2000, 2
    )
    conceptos = _items_by_concept(con_deducciones)
    assert conceptos["prestamo"]["amount"] == 800.0
    assert conceptos["infonavit"]["amount"] == 1200.0


def test_el_isr_se_calcula_sobre_la_base_gravable_no_sobre_el_total():
    result = PayrollService().process({
        "gross_salary": 21000,
        "christmas_bonus_days": 15
    })

    assert result["taxable_base"] < result["total_perceptions"]
    assert result["taxable_base"] == round(
        21000 + 10500 - UMA_DIARIA * 30, 2
    )


def test_el_bono_es_gravable_por_completo():
    result = PayrollService().process({"gross_salary": 10000, "bonus": 2000})

    bono = _items_by_concept(result)["bono"]
    assert bono["taxable"] == 2000.0
    assert bono["exempt"] == 0.0


def test_el_neto_cuadra_con_percepciones_menos_deducciones():
    result = PayrollService().process({
        "gross_salary": 21000,
        "overtime_double_hours": 9,
        "christmas_bonus_days": 15,
        "vacation_days": 12,
        "bonus": 1500,
        "loan_deduction": 800,
        "housing_credit_deduction": 1200
    })

    assert result["net_salary"] == round(
        result["total_perceptions"] - result["total_deductions"], 2
    )
    assert result["total_perceptions"] == round(
        sum(i["amount"] for i in result["items"] if i["kind"] == "perception"), 2
    )


def test_los_conceptos_negativos_se_rechazan():
    with pytest.raises(ValueError, match="no pueden ser negativos"):
        PayrollService().process({
            "gross_salary": 10000, "loan_deduction": -50
        })


def test_el_imss_se_topa_a_veinticinco_uma():
    service = PayrollService()

    assert service.process({"gross_salary": 500000})["imss_deduction"] == (
        service.process({"gross_salary": 1000000})["imss_deduction"]
    )


def test_la_tarifa_de_isr_escala_con_la_periodicidad():
    service = PayrollService()

    mensual = service.process({"gross_salary": 21000, "periodicity": "mensual"})
    quincenal = service.process({
        "gross_salary": 10500, "periodicity": "quincenal"
    })

    assert round(quincenal["isr_deduction"] * 2, 0) == round(
        mensual["isr_deduction"], 0
    )


def test_el_imss_tambien_escala_con_la_periodicidad():
    service = PayrollService()

    mensual = service.process({"gross_salary": 21000, "periodicity": "mensual"})
    quincenal = service.process({
        "gross_salary": 10500, "periodicity": "quincenal"
    })

    assert round(quincenal["imss_deduction"] * 2, 2) == round(
        mensual["imss_deduction"], 2
    )


def test_la_exencion_de_horas_extra_se_ajusta_a_las_semanas_del_periodo():
    service = PayrollService()

    mensual = service.process({
        "gross_salary": 60000, "periodicity": "mensual",
        "overtime_double_hours": 40
    })
    semanal = service.process({
        "gross_salary": 14000, "periodicity": "semanal",
        "overtime_double_hours": 40
    })

    tope_mensual = next(
        i for i in mensual["items"] if i["concept"] == "horas_extra"
    )["exempt"]
    tope_semanal = next(
        i for i in semanal["items"] if i["concept"] == "horas_extra"
    )["exempt"]

    assert tope_mensual > tope_semanal


def test_el_salario_diario_sale_de_los_dias_realmente_pagados():
    service = PayrollService()

    primera = service.process({
        "gross_salary": 10500, "periodicity": "quincenal",
        "paid_days": 15, "christmas_bonus_days": 15
    })
    segunda = service.process({
        "gross_salary": 10500, "periodicity": "quincenal",
        "paid_days": 16, "christmas_bonus_days": 15
    })

    aguinaldo_primera = next(
        i for i in primera["items"] if i["concept"] == "aguinaldo"
    )["amount"]
    aguinaldo_segunda = next(
        i for i in segunda["items"] if i["concept"] == "aguinaldo"
    )["amount"]

    assert aguinaldo_primera > aguinaldo_segunda


def test_una_periodicidad_desconocida_se_rechaza():
    with pytest.raises(ValueError, match="Periodicidad no reconocida"):
        PayrollService().process({
            "gross_salary": 10000, "periodicity": "decenal"
        })


def test_los_dias_pagados_deben_ser_positivos():
    with pytest.raises(ValueError, match="dias pagados"):
        PayrollService().process({"gross_salary": 10000, "paid_days": 0})


def test_la_periodicidad_viaja_en_el_resultado():
    result = PayrollService().process({
        "gross_salary": 10500, "periodicity": "quincenal", "paid_days": 15
    })

    assert result["periodicity"] == "quincenal"
    assert result["paid_days"] == 15
