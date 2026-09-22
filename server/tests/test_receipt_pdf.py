import re
import zlib
from datetime import date, datetime
from pathlib import Path

import pytest

from server.src.controllers import receipt_pdf
from server.src.controllers.receipt_pdf import (
    build_receipt_pdf,
    format_amount,
    build_receipt_response_headers,
    format_currency,
    format_date,
    format_period,
    format_range,
    receipt_filename,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def receipt():
    return {
        "id": 42,
        "employee_id": 3,
        "employee_name": "Ana López Ruiz",
        "employee_email": "ana@cen.com",
        "period_start": date(2026, 9, 1),
        "period_end": date(2026, 9, 30),
        "periodicity": "mensual",
        "paid_days": 30,
        "gross_salary": 21000,
        "isr_deduction": 2612.86,
        "imss_deduction": 583.0,
        "net_salary": 17804.14,
        "processed_by": "admin@cen.com",
        "created_at": datetime(2026, 9, 8, 10, 30),
    }


def test_format_currency_uses_thousands_and_two_decimals():
    assert format_currency(17804.14) == "$17,804.14"
    assert format_currency(0) == "$0.00"


def test_format_amount_drops_the_sign_for_the_ledger_columns():
    assert format_amount(21000) == "21,000.00"
    assert format_amount(583) == "583.00"


def test_format_period_reads_as_a_month():
    assert format_period(date(2026, 9, 1)) == "Septiembre de 2026"
    assert format_period(date(2026, 1, 1)) == "Enero de 2026"


def test_format_date_reads_as_a_day():
    assert format_date(datetime(2026, 9, 8, 10, 30)) == "8 de septiembre de 2026"


def test_build_receipt_pdf_returns_a_real_pdf(receipt):
    content = build_receipt_pdf(receipt)

    assert content.startswith(b"%PDF-")
    assert content.rstrip().endswith(b"%%EOF")
    assert len(content) > 1000


def test_build_receipt_pdf_survives_accents_in_the_name(receipt):
    receipt["employee_name"] = "Ana Sofía Muñoz Ñandú"

    content = build_receipt_pdf(receipt)

    assert content.startswith(b"%PDF-")


def test_build_receipt_pdf_accepts_decimal_amounts(receipt):
    from decimal import Decimal

    receipt["gross_salary"] = Decimal("21000.00")
    receipt["net_salary"] = Decimal("17804.14")

    content = build_receipt_pdf(receipt)

    assert content.startswith(b"%PDF-")


def test_receipt_filename_carries_the_folio_and_the_period(receipt):
    assert receipt_filename(receipt) == "recibo-42-2026-09-01.pdf"


def test_receipt_filename_pads_single_digit_months(receipt):
    receipt["period_start"] = date(2026, 1, 1)

    assert receipt_filename(receipt) == "recibo-42-2026-01-01.pdf"


def test_receipt_filename_distinguishes_the_two_fortnights(receipt):
    receipt["period_start"] = date(2026, 9, 16)

    assert receipt_filename(receipt) == "recibo-42-2026-09-16.pdf"


def test_format_range_within_one_month():
    assert format_range(date(2026, 9, 1), date(2026, 9, 15)) == (
        "1 al 15 de septiembre de 2026"
    )


def test_format_range_across_months():
    assert format_range(date(2026, 9, 28), date(2026, 10, 4)) == (
        "28 de septiembre al 4 de octubre de 2026"
    )


def test_response_headers_ask_the_browser_to_download(receipt):
    headers = build_receipt_response_headers(receipt)

    assert headers["Content-Disposition"] == (
        'attachment; filename="recibo-42-2026-09-01.pdf"'
    )


SKIN = ROOT / "client" / "src" / "styles" / "skin-base.css"


def _token(nombre: str) -> tuple:
    css = SKIN.read_text(encoding="utf-8")
    match = re.search(rf"{re.escape(nombre)}:\s*#([0-9a-fA-F]{{6}})\s*;", css)
    assert match, f"{nombre} ya no está en {SKIN.name}"
    crudo = match.group(1)
    return tuple(int(crudo[i:i + 2], 16) for i in (0, 2, 4))


def _drawn_text(receipt: dict) -> str:
    trozos = []
    for stream in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream",
                              build_receipt_pdf(receipt), re.S):
        trozos.append(zlib.decompress(stream.group(1)).decode("cp1252"))
    return "\n".join(trozos)


@pytest.mark.parametrize("constante, token", [
    (receipt_pdf.INK, "--rv-p-tinta-950"),
    (receipt_pdf.INK_2, "--rv-p-tinta-700"),
    (receipt_pdf.INK_3, "--rv-p-tinta-500"),
    (receipt_pdf.RULE, "--rv-p-hueso-400"),
    (receipt_pdf.RULE_SOFT, "--rv-p-hueso-200"),
    (receipt_pdf.MARCA, "--rv-p-jade-700"),
    (receipt_pdf.NETO, "--rv-p-jade-800"),
    (receipt_pdf.HUESO, "--rv-p-hueso-100"),
])
def test_the_palette_is_the_one_the_app_paints_with(constante, token):
    assert constante == _token(token)


def test_the_logo_repeats_the_geometry_of_logomark():
    trazos = []

    class Espia(receipt_pdf.ReceiptPDF):
        def rect(self, x, y, w, h, **kw):
            trazos.append(("rect", round(x, 2), round(y, 2),
                           round(w, 2), round(h, 2)))

        def polygon(self, point_list, **kw):
            trazos.append(("polygon",
                           [(round(px, 2), round(py, 2))
                            for px, py in point_list]))

    espia = Espia()
    espia.add_page()
    espia.logo(0, 0, 32)          # a escala 1: las cifras son las del SVG

    assert trazos == [
        ("rect", 0, 0, 32, 32),
        ("polygon", [(4.5, 4.0), (27.5, 4.0), (27.5, 7.6), (8.1, 7.6),
                     (8.1, 24.4), (27.5, 24.4), (27.5, 28.0), (4.5, 28.0)]),
        ("rect", 12, 11.7, 15.5, 3.4),
        ("rect", 12, 18.1, 15.5, 3.4),
    ]


def test_the_ledger_signs_the_amounts_like_the_app_does(receipt):
    texto = _drawn_text(receipt)

    assert "$21,000.00" in texto
    assert "\u2013 $2,612.86" in texto
    assert "\u2013 $583.00" in texto


def _fills(receipt: dict) -> list:
    colores = []
    for r, g, b in re.findall(
        r"([\d.]+) ([\d.]+) ([\d.]+) rg", _drawn_text(receipt)
    ):
        colores.append(tuple(round(float(c) * 255) for c in (r, g, b)))
    return colores


def test_the_net_is_the_only_thing_in_the_deep_green(receipt):
    assert _fills(receipt).count(receipt_pdf.NETO) == 1


def test_the_brand_green_is_the_logo_and_the_bar_of_the_net_block(receipt):
    assert _fills(receipt).count(receipt_pdf.MARCA) == 2


def test_a_name_with_typographic_punctuation_survives(receipt):
    receipt["employee_name"] = "Ana\u2019s O\u2019Brien Mu\u00f1oz"

    assert build_receipt_pdf(receipt).startswith(b"%PDF-")
