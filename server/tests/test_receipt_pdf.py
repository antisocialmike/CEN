from datetime import date, datetime

import pytest

from server.src.controllers.receipt_pdf import (
    build_receipt_pdf,
    build_receipt_response_headers,
    format_currency,
    format_date,
    format_period,
    receipt_filename,
)


@pytest.fixture
def receipt():
    return {
        "id": 42,
        "employee_id": 3,
        "employee_name": "Ana López Ruiz",
        "employee_email": "ana@cen.com",
        "period": date(2026, 9, 1),
        "gross_salary": 21000,
        "isr_deduction": 2612.86,
        "imss_deduction": 583.0,
        "net_salary": 17804.14,
        "processed_by": "admin@cen.com",
        "created_at": datetime(2026, 9, 8, 10, 30),
    }


def test_format_currency_uses_thousands_and_two_decimals():
    assert format_currency(17804.14) == "$ 17,804.14"
    assert format_currency(0) == "$ 0.00"


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
    assert receipt_filename(receipt) == "recibo-42-2026-09.pdf"


def test_receipt_filename_pads_single_digit_months(receipt):
    receipt["period"] = date(2026, 1, 1)

    assert receipt_filename(receipt) == "recibo-42-2026-01.pdf"


def test_response_headers_ask_the_browser_to_download(receipt):
    headers = build_receipt_response_headers(receipt)

    assert headers["Content-Disposition"] == (
        'attachment; filename="recibo-42-2026-09.pdf"'
    )
