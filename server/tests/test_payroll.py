from decimal import Decimal

import pytest
from server.src.controllers.employer_cost import (
    EmployerCostParameters,
    EmployerCostService,
    DAILY_DIVISOR,
)
from server.src.controllers.payroll_controller import (
    IMSSStrategy,
    ISRStrategy,
    MissingPayrollParameter,
    PayrollParameters,
    PayrollService,
)
from server.tests.payroll_parameters import (
    ISR_2025,
    ISR_2026,
    PARAMETERS_2025,
    PARAMETERS_2026,
    PAYROLL_RATES_2025,
    PAYROLL_RATES_2026,
    PAYROLL_RATES_ENERO_2025,
    PAYROLL_RATES_ENERO_2026,
)

UMA_DIARIA_2026 = 117.31


def _sbc(gross_salary, periodicity="mensual", rates=PAYROLL_RATES_2026, years=0):
    """El SBC que la ruta le pasa al calculo: el mismo del costo patronal."""
    if periodicity not in DAILY_DIVISOR:
        return 0.0
    return float(EmployerCostService().contribution_base(
        EmployerCostParameters(rates=rates), gross_salary, periodicity, years
    ))


def _process(inputs, parameters=PARAMETERS_2026, rates=PAYROLL_RATES_2026):
    periodicity = inputs.get("periodicity") or "mensual"
    return PayrollService().process(
        inputs, parameters, _sbc(inputs.get("gross_salary", 0), periodicity, rates)
    )


def _items_by_concept(result):
    return {item["concept"]: item for item in result["items"]}


# --- Parametros con vigencia ---------------------------------------------------

def test_el_subsidio_de_2026_es_el_15_02_por_ciento_de_la_uma():
    # 15.02% de 3,566.22 (decreto DOF 31-12-2025).
    assert PARAMETERS_2026.subsidio_mensual == 535.65


def test_en_enero_de_2026_el_subsidio_usa_la_uma_2025_y_su_porcentaje():
    enero = PayrollParameters.from_rows(PAYROLL_RATES_ENERO_2026, ISR_2026)

    # 15.59% de 3,439.46.
    assert enero.subsidio_mensual == 536.21


def test_el_subsidio_de_2025_y_su_enero():
    enero = PayrollParameters.from_rows(PAYROLL_RATES_ENERO_2025, ISR_2025)

    # 13.8% de 3,439.46 y, en enero, 14.39% de la UMA 2024 (3,300.53).
    assert PARAMETERS_2025.subsidio_mensual == 474.65
    assert enero.subsidio_mensual == 474.95


@pytest.mark.parametrize("key", [
    "uma_diaria",
    "salario_minimo_general",
    "subsidio_empleo_porcentaje_uma",
    "subsidio_empleo_limite_mensual",
])
def test_sin_un_parametro_vigente_no_se_calcula(key):
    rates = {k: v for k, v in PAYROLL_RATES_2026.items() if k != key}

    with pytest.raises(MissingPayrollParameter) as error:
        PayrollParameters.from_rows(rates, ISR_2026)

    assert error.value.name == key


def test_sin_tarifa_de_isr_vigente_no_se_calcula():
    with pytest.raises(MissingPayrollParameter) as error:
        PayrollParameters.from_rows(PAYROLL_RATES_2026, [])

    assert error.value.name == "tarifa_isr"


# --- ISR --------------------------------------------------------------------

def test_isr_calculation():
    # 420.95 + (10,000 - 7,168.52) x 10.88% = 729.02, menos 535.65 de subsidio.
    assert ISRStrategy(PARAMETERS_2026).calculate(10000) == 193.37


def test_isr_calculation_bajo_limite_de_subsidio():
    assert ISRStrategy(PARAMETERS_2026).calculate(5000) == 0.0


def test_el_isr_de_2025_usa_su_propia_tarifa_y_su_subsidio():
    # 371.83 + (10,000 - 6,332.06) x 10.88% = 770.90, menos 474.65 de subsidio.
    assert ISRStrategy(PARAMETERS_2025).calculate(10000) == 296.25


def test_arriba_del_limite_no_hay_subsidio():
    # 1,011.68 + (12,600 - 12,598.03) x 16%: pasa de 11,492.66, sin subsidio.
    assert ISRStrategy(PARAMETERS_2026).calculate(12600) == 1012.0


# --- IMSS: cuota obrera sobre el SBC ----------------------------------------

def test_imss_calculation():
    # SBC 349.77 (333.33 x 1.049315) x 30 dias x 2.375%.
    assert IMSSStrategy(PARAMETERS_2026).calculate(349.77, 30) == 249.21


def test_imss_calculation_con_excedente_de_3_uma():
    # SBC 699.55: 699.55 x 30 x 2.375% + (699.55 - 351.93) x 30 x 0.40%.
    assert IMSSStrategy(PARAMETERS_2026).calculate(699.55, 30) == 540.14


def test_el_imss_se_calcula_sobre_el_sbc_no_sobre_el_sueldo():
    result = _process({"gross_salary": 10000})

    # Sobre el sueldo serian 10,000 x 2.375% = 237.50; el SBC integra aguinaldo
    # y prima vacacional.
    assert result["imss_deduction"] == 249.21


def test_el_imss_cuenta_los_dias_del_periodo():
    treinta = _process({"gross_salary": 10000, "paid_days": 30})
    treinta_y_uno = _process({"gross_salary": 10000, "paid_days": 31})

    assert treinta_y_uno["imss_deduction"] > treinta["imss_deduction"]


def test_el_imss_se_topa_a_veinticinco_uma():
    assert _process({"gross_salary": 500000})["imss_deduction"] == (
        _process({"gross_salary": 1000000})["imss_deduction"]
    )


# --- Salario minimo ---------------------------------------------------------

def test_a_quien_gana_el_salario_minimo_no_se_le_retiene_nada():
    # 315.04 x 30: el salario minimo general de 2026.
    result = _process({"gross_salary": 9451.20})

    conceptos = _items_by_concept(result)
    assert result["isr_deduction"] == 0.0
    assert result["imss_deduction"] == 0.0
    assert result["net_salary"] == 9451.20
    assert "salario minimo" in conceptos["isr"]["description"]
    assert "patron" in conceptos["imss"]["description"]


def test_su_cuota_del_imss_la_paga_el_patron():
    result = _process({"gross_salary": 9451.20})

    # SBC 330.58 (315.04 x 1.049315) x 30 dias x 2.375%.
    assert result["imss_employer_paid"] == 235.54


def test_con_percepciones_extra_el_isr_si_se_calcula():
    result = _process({"gross_salary": 9451.20, "bonus": 2000})

    # 420.95 + (11,451.20 - 7,168.52) x 10.88% = 886.91, menos 535.65.
    assert result["isr_deduction"] == 351.26
    # La cuota del IMSS la sigue pagando el patron: depende del salario diario.
    assert result["imss_deduction"] == 0.0


def test_un_peso_arriba_del_minimo_ya_retiene():
    result = _process({"gross_salary": 9500})

    assert result["imss_deduction"] > 0
    assert result["imss_employer_paid"] == 0.0


def test_el_minimo_de_2025_es_otro():
    # 9,451.20 en 2025 ya no es el minimo (278.80 x 30 = 8,364.00).
    result = _process(
        {"gross_salary": 9451.20}, PARAMETERS_2025, PAYROLL_RATES_2025
    )

    assert result["imss_deduction"] > 0


# --- El desglose ------------------------------------------------------------

def test_una_nomina_sin_conceptos_extra_solo_lleva_sueldo_isr_e_imss():
    result = _process({"gross_salary": 10000})

    assert list(_items_by_concept(result)) == ["sueldo", "isr", "imss"]
    assert result["total_perceptions"] == 10000
    # 10,000 - 193.37 de ISR - 249.21 de IMSS.
    assert result["net_salary"] == 9557.42


def test_process_negative_value_raises_error():
    with pytest.raises(ValueError, match="El salario no puede ser negativo"):
        _process({"gross_salary": -500})


def test_horas_extra_dobles_y_triples_segun_la_ley_federal_del_trabajo():
    result = _process({
        "gross_salary": 21000,
        "overtime_double_hours": 9,
        "overtime_triple_hours": 3
    })

    horas = _items_by_concept(result)["horas_extra"]
    assert horas["amount"] == 2362.5
    assert horas["taxable"] + horas["exempt"] == horas["amount"]


def test_la_mitad_de_las_horas_extra_esta_exenta():
    result = _process({
        "gross_salary": 21000,
        "overtime_double_hours": 4
    })

    horas = _items_by_concept(result)["horas_extra"]
    assert horas["exempt"] == round(horas["amount"] * 0.5, 2)


def test_el_aguinaldo_sale_de_los_dias_de_salario_diario():
    result = _process({
        "gross_salary": 21000,
        "christmas_bonus_days": 15
    })

    aguinaldo = _items_by_concept(result)["aguinaldo"]
    assert aguinaldo["amount"] == 10500.0
    assert aguinaldo["exempt"] == round(UMA_DIARIA_2026 * 30, 2)


def test_la_exencion_del_aguinaldo_usa_la_uma_del_periodo():
    result = _process(
        {"gross_salary": 21000, "christmas_bonus_days": 15},
        PayrollParameters.from_rows(PAYROLL_RATES_ENERO_2026, ISR_2026),
        PAYROLL_RATES_ENERO_2026,
    )

    # En enero de 2026 rige la UMA 2025: 113.14 x 30.
    assert _items_by_concept(result)["aguinaldo"]["exempt"] == 3394.2


def test_el_aguinaldo_pequeno_queda_totalmente_exento():
    result = _process({
        "gross_salary": 6000,
        "christmas_bonus_days": 15
    })

    aguinaldo = _items_by_concept(result)["aguinaldo"]
    assert aguinaldo["amount"] == 3000.0
    assert aguinaldo["taxable"] == 0.0
    assert aguinaldo["exempt"] == 3000.0


def test_la_prima_vacacional_es_el_veinticinco_por_ciento():
    result = _process({
        "gross_salary": 21000,
        "vacation_days": 12
    })

    prima = _items_by_concept(result)["prima_vacacional"]
    assert prima["amount"] == 2100.0
    assert prima["exempt"] == round(UMA_DIARIA_2026 * 15, 2)


def test_las_deducciones_adicionales_se_restan_del_neto():
    sin_deducciones = _process({"gross_salary": 21000})
    con_deducciones = _process({
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
    result = _process({
        "gross_salary": 21000,
        "christmas_bonus_days": 15
    })

    assert result["taxable_base"] < result["total_perceptions"]
    assert result["taxable_base"] == round(
        21000 + 10500 - UMA_DIARIA_2026 * 30, 2
    )


def test_el_bono_es_gravable_por_completo():
    result = _process({"gross_salary": 10000, "bonus": 2000})

    bono = _items_by_concept(result)["bono"]
    assert bono["taxable"] == 2000.0
    assert bono["exempt"] == 0.0


def test_el_neto_cuadra_con_percepciones_menos_deducciones():
    result = _process({
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
        _process({"gross_salary": 10000, "loan_deduction": -50})


def test_la_tarifa_de_isr_escala_con_la_periodicidad():
    mensual = _process({"gross_salary": 21000, "periodicity": "mensual"})
    quincenal = _process({"gross_salary": 10500, "periodicity": "quincenal"})

    assert round(quincenal["isr_deduction"] * 2, 0) == round(
        mensual["isr_deduction"], 0
    )


def test_el_imss_tambien_escala_con_la_periodicidad():
    mensual = _process({"gross_salary": 21000, "periodicity": "mensual"})
    quincenal = _process({"gross_salary": 10500, "periodicity": "quincenal"})

    assert round(quincenal["imss_deduction"] * 2, 2) == round(
        mensual["imss_deduction"], 2
    )


def test_la_exencion_de_horas_extra_se_ajusta_a_las_semanas_del_periodo():
    mensual = _process({
        "gross_salary": 60000, "periodicity": "mensual",
        "overtime_double_hours": 40
    })
    semanal = _process({
        "gross_salary": 14000, "periodicity": "semanal",
        "overtime_double_hours": 40
    })

    tope_mensual = _items_by_concept(mensual)["horas_extra"]["exempt"]
    tope_semanal = _items_by_concept(semanal)["horas_extra"]["exempt"]

    assert tope_mensual > tope_semanal


def test_el_salario_diario_sale_de_los_dias_realmente_pagados():
    primera = _process({
        "gross_salary": 10500, "periodicity": "quincenal",
        "paid_days": 15, "christmas_bonus_days": 15
    })
    segunda = _process({
        "gross_salary": 10500, "periodicity": "quincenal",
        "paid_days": 16, "christmas_bonus_days": 15
    })

    aguinaldo_primera = _items_by_concept(primera)["aguinaldo"]["amount"]
    aguinaldo_segunda = _items_by_concept(segunda)["aguinaldo"]["amount"]

    assert aguinaldo_primera > aguinaldo_segunda


def test_una_periodicidad_desconocida_se_rechaza():
    with pytest.raises(ValueError, match="Periodicidad no reconocida"):
        _process({"gross_salary": 10000, "periodicity": "decenal"})


def test_los_dias_pagados_deben_ser_positivos():
    with pytest.raises(ValueError, match="dias pagados"):
        _process({"gross_salary": 10000, "paid_days": 0})


def test_la_periodicidad_viaja_en_el_resultado():
    result = _process({
        "gross_salary": 10500, "periodicity": "quincenal", "paid_days": 15
    })

    assert result["periodicity"] == "quincenal"
    assert result["paid_days"] == 15


def test_el_sbc_se_redondea_como_el_costo_patronal():
    # La ruta le pasa al calculo el SBC en Decimal ya redondeado.
    assert _sbc(10000) == float(Decimal("349.77"))


# --- Asimilados a salarios (tipo de regimen 09) -----------------------------

def _asimilado(inputs):
    return _process({**inputs, "tipo_regimen": "09"})


def test_un_asimilado_paga_isr_sin_subsidio_y_no_cotiza_al_imss():
    result = _asimilado({"gross_salary": 10000})

    # 420.95 + (10,000 - 7,168.52) x 10.88% = 729.02: sin restar subsidio.
    assert result["isr_deduction"] == 729.02
    assert result["imss_deduction"] == 0.0
    assert result["net_salary"] == 9270.98
    assert result["tipo_regimen"] == "09"
    assert list(_items_by_concept(result)) == ["sueldo", "isr"]


def test_su_percepcion_se_llama_honorarios_asimilados():
    result = _asimilado({"gross_salary": 10000})

    assert _items_by_concept(result)["sueldo"]["description"] == (
        "Honorarios asimilados a salarios del periodo"
    )


def test_el_salario_minimo_no_aplica_a_un_asimilado():
    result = _asimilado({"gross_salary": 9451.20})

    # 420.95 + (9,451.20 - 7,168.52) x 10.88% = 669.31, sin subsidio.
    assert result["isr_deduction"] == 669.31
    assert result["imss_employer_paid"] == 0.0


@pytest.mark.parametrize("concepto", [
    "overtime_double_hours",
    "overtime_triple_hours",
    "christmas_bonus_days",
    "vacation_days",
    "housing_credit_deduction",
])
def test_un_asimilado_no_tiene_prestaciones_de_la_relacion_laboral(concepto):
    with pytest.raises(ValueError, match="asimilado"):
        _asimilado({"gross_salary": 10000, concepto: 1})


def test_un_asimilado_si_puede_tener_bono_y_prestamo():
    result = _asimilado({
        "gross_salary": 10000, "bonus": 2000, "loan_deduction": 500,
    })

    conceptos = _items_by_concept(result)
    assert conceptos["bono"]["taxable"] == 2000.0
    assert conceptos["prestamo"]["amount"] == 500.0


def test_sin_tipo_de_regimen_la_nomina_es_de_sueldos():
    assert _process({"gross_salary": 10000})["tipo_regimen"] == "02"


@pytest.mark.parametrize("campo, valor", [
    ("tipo_regimen", "05"), ("tipo_jornada", "04"),
])
def test_un_regimen_o_una_jornada_que_no_se_manejan_se_rechazan(campo, valor):
    with pytest.raises(ValueError, match="no reconocido"):
        _process({"gross_salary": 10000, campo: valor})


# --- Jornada (LFT art. 61) --------------------------------------------------

@pytest.mark.parametrize("jornada, importe", [
    # 21,000 / 30 = 700 diarios; 9 horas dobles.
    ("01", 1575.0),   # 700 / 8 = 87.50 la hora
    ("02", 1800.0),   # 700 / 7 = 100.00 la hora
    ("03", 1680.0),   # 700 / 7.5 = 93.33 la hora
])
def test_la_hora_extra_sale_de_la_jornada_de_cada_quien(jornada, importe):
    result = _process({
        "gross_salary": 21000, "overtime_double_hours": 9,
        "tipo_jornada": jornada,
    })

    assert _items_by_concept(result)["horas_extra"]["amount"] == importe
