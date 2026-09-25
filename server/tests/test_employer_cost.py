"""Costo patronal con casos calculados a mano.

Parametros de septiembre de 2026: UMA 117.31, salario minimo 315.04, tabla de
cesantia y vejez de 2026 y prima de riesgo de clase I (0.54355%). Un mes de
30 dias. El factor de integracion del primer anio es
(365 + 15 de aguinaldo + 12 de vacaciones x 25%) / 365 = 383 / 365 = 1.049315.
"""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from server.src.controllers.employer_cost import (
    EmployerCostInputs,
    EmployerCostParameters,
    EmployerCostService,
    RetirementUnemploymentOldAge,
    CostContext,
    completed_years,
    vacation_days,
)

D = Decimal

CEAV_2026 = [
    {"minimum_wage": True, "upper_uma": None, "rate": D("0.03150")},
    {"minimum_wage": False, "upper_uma": D("1.50"), "rate": D("0.03676")},
    {"minimum_wage": False, "upper_uma": D("2.00"), "rate": D("0.04851")},
    {"minimum_wage": False, "upper_uma": D("2.50"), "rate": D("0.05556")},
    {"minimum_wage": False, "upper_uma": D("3.00"), "rate": D("0.06026")},
    {"minimum_wage": False, "upper_uma": D("3.50"), "rate": D("0.06361")},
    {"minimum_wage": False, "upper_uma": D("4.00"), "rate": D("0.06613")},
    {"minimum_wage": False, "upper_uma": None, "rate": D("0.07513")},
]

RATES_2026 = {
    "uma_diaria": D("117.31"),
    "salario_minimo_general": D("315.04"),
    "imss_em_cuota_fija": D("0.204"),
    "imss_em_excedente": D("0.011"),
    "imss_em_excedente_umbral_uma": D("3"),
    "imss_em_prestaciones_dinero": D("0.007"),
    "imss_gastos_medicos_pensionados": D("0.0105"),
    "imss_invalidez_vida": D("0.0175"),
    "imss_guarderias": D("0.01"),
    "imss_retiro": D("0.02"),
    "imss_tope_uma": D("25"),
    "infonavit": D("0.05"),
    "lft_aguinaldo_dias": D("15"),
    "lft_prima_vacacional": D("0.25"),
}


def _params(isn=D("0.03"), risk=D("0.0054355"), **rates) -> EmployerCostParameters:
    return EmployerCostParameters(
        rates={**RATES_2026, **rates},
        ceav_brackets=CEAV_2026,
        isn_rate=isn,
        risk_rate=risk,
    )


def _inputs(monthly: str, years: int = 0) -> EmployerCostInputs:
    return EmployerCostInputs(
        period_salary=D(monthly),
        periodicity="mensual",
        days=D(30),
        years_completed=years,
        total_perceptions=D(monthly),
    )


def _amounts(result: dict) -> dict:
    return {item["component"]: item["amount"] for item in result["items"]}


service = EmployerCostService()


# --- Factor de integracion y vacaciones --------------------------------------

@pytest.mark.parametrize("years, days", [
    (0, 12), (1, 14), (2, 16), (3, 18), (4, 20),
    (5, 22), (9, 22), (10, 24), (15, 26), (20, 28), (25, 30), (30, 32),
])
def test_vacation_days_follow_the_2022_reform(years, days):
    assert vacation_days(years) == days


@pytest.mark.parametrize("years, factor", [
    (0, D("1.049315")),   # (365 + 15 + 12 x 0.25) / 365
    (5, D("1.056164")),   # (365 + 15 + 22 x 0.25) / 365
])
def test_integration_factor(years, factor):
    assert service.integration_factor(_params(), years) == factor


def test_completed_years_counts_whole_anniversaries():
    hired = datetime(2021, 9, 15, tzinfo=timezone.utc)

    assert completed_years(hired, date(2026, 9, 14)) == 4
    assert completed_years(hired, date(2026, 9, 15)) == 5
    assert completed_years(None, date(2026, 9, 15)) == 0


# --- Salario minimo ----------------------------------------------------------

def test_minimum_wage_worker():
    # Diario 9,451.20 / 30 = 315.04; SBC = 315.04 x 1.049315 = 330.58
    # (2.82 UMA -> rango 2.51 a 3.00, 6.026%). Base = 330.58 x 30 = 9,917.40.
    result = service.calculate(_inputs("9451.20"), _params())

    assert result["daily_salary"] == D("315.04")
    assert result["sbc_daily"] == D("330.58")
    assert _amounts(result) == {
        "em_cuota_fija": D("717.94"),           # 117.31 x 30 x 20.40%
        "em_excedente": D("0.00"),              # SBC bajo 3 UMA (351.93)
        "em_prestaciones_dinero": D("69.42"),   # 9,917.40 x 0.70%
        "gastos_medicos_pensionados": D("104.13"),  # x 1.05%
        "invalidez_vida": D("173.55"),          # x 1.75%
        "riesgo_trabajo": D("53.91"),           # x 0.54355%
        "guarderias": D("99.17"),               # x 1%
        "retiro": D("198.35"),                  # x 2%
        "ceav": D("597.62"),                    # x 6.026%
        "infonavit": D("495.87"),               # x 5%
        "isn": D("283.54"),                     # 9,451.20 x 3%
    }
    assert result["total"] == D("2793.50")
    assert result["missing"] == []


# --- Tope de 25 UMA ----------------------------------------------------------

def test_salary_above_the_25_uma_ceiling():
    # Diario 5,000 x 1.049315 = 5,246.58, topado a 25 x 117.31 = 2,932.75.
    result = service.calculate(_inputs("150000.00"), _params())

    assert result["sbc_daily"] == D("2932.75")
    amounts = _amounts(result)
    # Excedente: (2,932.75 - 351.93) x 30 = 77,424.60 x 1.10%
    assert amounts["em_excedente"] == D("851.67")
    assert amounts["ceav"] == D("6610.13")      # 87,982.50 x 7.513%
    assert amounts["infonavit"] == D("4399.13")
    assert result["total"] == D("23275.97")


# --- ISN de dos estados ------------------------------------------------------

def test_two_states_with_different_payroll_tax():
    # Mismo sueldo de 40,000: SBC = 1,333.33 x 1.049315 = 1,399.08.
    at_2 = service.calculate(_inputs("40000.00"), _params(isn=D("0.02")))
    at_3 = service.calculate(_inputs("40000.00"), _params(isn=D("0.03")))

    assert _amounts(at_2)["isn"] == D("800.00")
    assert _amounts(at_3)["isn"] == D("1200.00")
    assert at_2["total"] == D("10071.86")
    assert at_3["total"] - at_2["total"] == D("400.00")
    assert _amounts(at_2)["em_excedente"] == D("345.56")  # 31,414.50 x 1.10%


# --- Cesantia y vejez: un salario en cada rango ------------------------------

def _ceav_rate(sbc: str, minimum_wage: str) -> Decimal:
    params = _params(salario_minimo_general=D(minimum_wage))
    ctx = CostContext(
        params=params, inputs=_inputs("1"), sbc=D(sbc), uma=D("117.31")
    )
    return RetirementUnemploymentOldAge().rate_for(ctx, D(sbc))


@pytest.mark.parametrize("sbc, rate", [
    # En 2026 el minimo ya vale 2.69 UMA, asi que los rangos bajos no se
    # alcanzan con el minimo real: se baja a 100 solo para recorrer la tabla.
    ("140.77", "0.03676"),   # 1.20 UMA
    ("175.97", "0.03676"),   # 1.50 UMA, limite superior incluido
    ("176.57", "0.04851"),   # 1.505 UMA se redondea a 1.51
    ("269.81", "0.05556"),   # 2.30 UMA
    ("328.47", "0.06026"),   # 2.80 UMA
    ("375.39", "0.06361"),   # 3.20 UMA
    ("445.78", "0.06613"),   # 3.80 UMA
    ("586.55", "0.07513"),   # 5.00 UMA
])
def test_ceav_rate_for_each_bracket(sbc, rate):
    assert _ceav_rate(sbc, minimum_wage="100.00") == D(rate)


def test_ceav_minimum_wage_row():
    assert _ceav_rate("315.04", minimum_wage="315.04") == D("0.03150")


# --- Parametros que faltan ----------------------------------------------------

def test_missing_parameters_stay_out_of_the_total():
    result = service.calculate(
        _inputs("9451.20"), _params(isn=None, risk=None)
    )

    assert result["missing"] == ["prima_riesgo_trabajo", "isn"]
    assert "riesgo_trabajo" not in _amounts(result)
    # 2,793.50 - 53.91 de riesgo - 283.54 de ISN
    assert result["total"] == D("2456.05")


def test_without_uma_nothing_that_depends_on_the_sbc_is_computed():
    params = _params()
    del params.rates["uma_diaria"]

    result = service.calculate(_inputs("9451.20"), params)

    assert result["sbc_daily"] is None
    assert set(_amounts(result)) == {"isn"}
    assert "uma_diaria" in result["missing"]


def test_every_component_names_its_group():
    groups = {
        item["component"]: item["group_key"]
        for item in service.calculate(_inputs("9451.20"), _params())["items"]
    }

    assert groups["retiro"] == groups["ceav"] == "sar"
    assert groups["infonavit"] == "infonavit"
    assert groups["isn"] == "isn"
    assert groups["em_cuota_fija"] == groups["riesgo_trabajo"] == "imss"
