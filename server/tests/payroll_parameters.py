"""Los parametros que siembran las migraciones 012 y 013, para las pruebas.

No es un archivo de pruebas: lo importan las que necesitan calcular una nomina.
"""
from decimal import Decimal as D

from server.src.controllers.payroll_controller import PayrollParameters
from server.tests.test_employer_cost import RATES_2026


def _tarifa(renglones):
    return [
        {"lower_limit": D(li), "upper_limit": None if ls is None else D(ls),
         "fixed_fee": D(cuota), "rate": D(tasa)}
        for li, ls, cuota, tasa in renglones
    ]


# Anexo 8 RMF 2026, apartado V.
ISR_2026 = _tarifa([
    ("0.00", "844.59", "0.00", "0.0192"),
    ("844.60", "7168.51", "16.22", "0.0640"),
    ("7168.52", "12598.02", "420.95", "0.1088"),
    ("12598.03", "14644.64", "1011.68", "0.1600"),
    ("14644.65", "17533.64", "1339.14", "0.1792"),
    ("17533.65", "35362.83", "1856.84", "0.2136"),
    ("35362.84", "55736.68", "5665.16", "0.2352"),
    ("55736.69", "106410.50", "10457.09", "0.3000"),
    ("106410.51", "141880.66", "25659.23", "0.3200"),
    ("141880.67", "425641.99", "37009.69", "0.3400"),
    ("425642.00", None, "133488.54", "0.3500"),
])

# Anexo 8 RMF 2025, apartado V.
ISR_2025 = _tarifa([
    ("0.00", "746.04", "0.00", "0.0192"),
    ("746.05", "6332.05", "14.32", "0.0640"),
    ("6332.06", "11128.01", "371.83", "0.1088"),
    ("11128.02", "12935.82", "893.63", "0.1600"),
    ("12935.83", "15487.71", "1182.88", "0.1792"),
    ("15487.72", "31236.49", "1640.18", "0.2136"),
    ("31236.50", "49233.00", "5004.12", "0.2352"),
    ("49233.01", "93993.90", "9236.89", "0.3000"),
    ("93993.91", "125325.20", "22665.17", "0.3200"),
    ("125325.21", "375975.61", "32691.18", "0.3400"),
    ("375975.62", None, "117912.32", "0.3500"),
])

# De febrero a diciembre de 2026.
PAYROLL_RATES_2026 = {
    **RATES_2026,
    "subsidio_empleo_porcentaje_uma": D("0.1502"),
    "subsidio_empleo_limite_mensual": D("11492.66"),
}

# Enero de 2026: todavia rige la UMA 2025, con el porcentaje de transicion.
PAYROLL_RATES_ENERO_2026 = {
    **PAYROLL_RATES_2026,
    "uma_diaria": D("113.14"),
    "subsidio_empleo_porcentaje_uma": D("0.1559"),
}

# De febrero a diciembre de 2025.
PAYROLL_RATES_2025 = {
    **RATES_2026,
    "uma_diaria": D("113.14"),
    "salario_minimo_general": D("278.80"),
    "subsidio_empleo_porcentaje_uma": D("0.138"),
    "subsidio_empleo_limite_mensual": D("10171.00"),
}

# Enero de 2025: UMA 2024 y el porcentaje de transicion de ese decreto.
PAYROLL_RATES_ENERO_2025 = {
    **PAYROLL_RATES_2025,
    "uma_diaria": D("108.57"),
    "subsidio_empleo_porcentaje_uma": D("0.1439"),
}

PARAMETERS_2026 = PayrollParameters.from_rows(PAYROLL_RATES_2026, ISR_2026)
PARAMETERS_2025 = PayrollParameters.from_rows(PAYROLL_RATES_2025, ISR_2025)

# Solo lo que necesita el calculo de la nomina: sin las tasas del costo
# patronal, sus componentes quedan pendientes. Para las pruebas de rutas que no
# miran el costo patronal.
PAYROLL_ONLY_RATES_2026 = {
    key: PAYROLL_RATES_2026[key]
    for key in (
        "uma_diaria",
        "salario_minimo_general",
        "subsidio_empleo_porcentaje_uma",
        "subsidio_empleo_limite_mensual",
        "lft_aguinaldo_dias",
        "lft_prima_vacacional",
        "imss_tope_uma",
    )
}
