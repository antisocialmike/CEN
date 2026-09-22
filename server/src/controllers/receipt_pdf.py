from fpdf import FPDF

COMPANY_NAME = "CEN Payroll"
COMPANY_EYEBROW = "COMPROBANTE DE NÓMINA"
DISCLAIMER = (
    "Comprobante interno de nómina. No es un CFDI y no tiene validez fiscal "
    "ante el SAT."
)

MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

INK = (16, 17, 20)
INK_2 = (74, 78, 87)
INK_3 = (95, 100, 110)
RULE = (189, 183, 169)
RULE_SOFT = (233, 229, 218)
MARCA = (14, 124, 102)
NETO = (12, 97, 89)
HUESO = (244, 242, 236)
BLANCO = (255, 255, 255)

PAGE_FORMAT = "Letter"
PAGE_WIDTH = 215.9
PAGE_HEIGHT = 279.4
MARGIN = 24.0
CONTENT = PAGE_WIDTH - MARGIN * 2
SETTLEMENT_ANCHOR = PAGE_HEIGHT - 92

MINUS = "–"

LOGO_SIZE = 9.6
LOGO_GRID = 32.0


def _tracking(em: float, size_pt: float) -> float:
    return em * size_pt * 25.4 / 72.0


def format_amount(amount) -> str:
    return "{:,.2f}".format(float(amount))


def format_currency(amount) -> str:
    return "$" + format_amount(amount)


PERIODICITY_LABELS = {
    "mensual": "Mensual",
    "quincenal": "Quincenal",
    "semanal": "Semanal",
}


def format_period(period) -> str:
    return "{} de {}".format(MONTHS[period.month - 1].capitalize(), period.year)


def format_range(start, end) -> str:
    if start.month == end.month:
        return "{} al {} de {} de {}".format(
            start.day, end.day, MONTHS[start.month - 1], start.year
        )
    return "{} de {} al {} de {} de {}".format(
        start.day, MONTHS[start.month - 1],
        end.day, MONTHS[end.month - 1], start.year
    )


def format_date(moment) -> str:
    return "{} de {} de {}".format(
        moment.day, MONTHS[moment.month - 1], moment.year
    )


class ReceiptPDF(FPDF):
    def tracked(self, text: str, em: float, size_pt: float, height: float,
                width=0, align="L") -> None:
        self.set_char_spacing(_tracking(em, size_pt))
        self.cell(width, height, text, new_x="LMARGIN", new_y="NEXT",
                  align=align)
        self.set_char_spacing(0)

    def eyebrow(self, text: str, color=INK_3) -> None:
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*color)
        self.tracked(text.upper(), 0.09, 7.5, 4)

    def rule(self, color=RULE, width=CONTENT, thickness=0.2) -> None:
        self.set_draw_color(*color)
        self.set_line_width(thickness)
        y = self.get_y()
        self.line(MARGIN, y, MARGIN + width, y)
        self.set_line_width(0.2)

    def logo(self, x: float, y: float, size: float = LOGO_SIZE) -> None:
        k = size / LOGO_GRID

        self.set_fill_color(*MARCA)
        self.rect(x, y, size, size, style="F")

        bracket = [
            (4.5, 4.0), (27.5, 4.0), (27.5, 7.6), (8.1, 7.6),
            (8.1, 24.4), (27.5, 24.4), (27.5, 28.0), (4.5, 28.0),
        ]
        self.set_fill_color(*BLANCO)
        self.polygon([(x + px * k, y + py * k) for px, py in bracket],
                     style="F")

        for bar_y in (11.7, 18.1):
            self.rect(x + 12.0 * k, y + bar_y * k, 15.5 * k, 3.4 * k,
                      style="F")

    def masthead(self, folio: str) -> None:
        top = self.get_y()
        self.logo(MARGIN, top)

        text_x = MARGIN + LOGO_SIZE + 4.2
        self.set_xy(text_x, top + 0.6)
        self.set_font("Helvetica", "B", 11.5)
        self.set_text_color(*INK)
        self.set_char_spacing(_tracking(-0.03, 11.5))
        self.cell(CONTENT * 0.6, 5, COMPANY_NAME, new_x="LMARGIN",
                  new_y="NEXT")
        self.set_char_spacing(0)

        self.set_xy(text_x, top + 5.4)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*INK_3)
        self.set_char_spacing(_tracking(0.09, 7))
        self.cell(CONTENT * 0.6, 4, COMPANY_EYEBROW)
        self.set_char_spacing(0)

        self.set_font("Helvetica", "", 8)
        self.set_text_color(*INK_3)
        self.set_char_spacing(_tracking(0.06, 8))
        self.cell(0, 4, folio.upper(), align="R", new_x="LMARGIN",
                  new_y="NEXT")
        self.set_char_spacing(0)

        self.set_y(top + LOGO_SIZE + 5)
        self.rule(RULE)

    def identity(self, receipt: dict) -> None:
        self.ln(13)
        self.eyebrow("Periodo")

        self.ln(0.5)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*INK)
        self.tracked(format_period(receipt["period_start"]), -0.025, 28, 12)

        self.ln(0.5)
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*INK_2)
        self.cell(0, 5, "{}, {}".format(
            PERIODICITY_LABELS.get(receipt.get("periodicity"), "Periodo"),
            format_range(receipt["period_start"], receipt["period_end"]),
        ), new_x="LMARGIN", new_y="NEXT")

        self.ln(7)
        self.eyebrow("Empleado")

        self.ln(0.5)
        self.set_font("Helvetica", "", 12.5)
        self.set_text_color(*INK)
        self.cell(0, 6, str(receipt["employee_name"]), new_x="LMARGIN",
                  new_y="NEXT")

        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*INK_3)
        self.cell(0, 4.5, str(receipt["employee_email"]), new_x="LMARGIN",
                  new_y="NEXT")

    def leader(self, from_x: float, to_x: float, y: float) -> None:
        if to_x - from_x < 3:
            return
        self.set_draw_color(*RULE)
        self.set_line_width(0.15)
        self.set_dash_pattern(dash=0.5, gap=0.8)
        self.line(from_x, y, to_x, y)
        self.set_dash_pattern()

    def ledger_row(self, label: str, amount: str, bold: bool, indent: float,
                   label_color, amount_color) -> None:
        y = self.get_y()

        self.set_font("Helvetica", "B" if bold else "", 11 if bold else 10)
        self.set_text_color(*label_color)
        label_x = MARGIN + indent
        self.set_xy(label_x, y)
        self.cell(self.get_string_width(label), 6, label)
        label_end = label_x + self.get_string_width(label)

        self.set_font("Helvetica", "B" if bold else "", 11 if bold else 10)
        self.set_text_color(*amount_color)
        amount_width = self.get_string_width(amount)
        amount_x = MARGIN + CONTENT - amount_width

        self.leader(label_end + 1.8, amount_x - 1.8, y + 3.6)

        self.set_xy(amount_x, y)
        self.cell(amount_width, 6, amount, new_x="LMARGIN", new_y="NEXT")

    def ledger_group(self, title: str, total, items: list,
                     negative: bool) -> None:
        sign = MINUS + " " if negative else ""

        self.ledger_row(title, sign + format_currency(total), True, 0,
                        INK, INK)
        self.ln(0.5)
        self.rule(RULE_SOFT)
        self.ln(1.5)

        for label, amount in items:
            self.ledger_row(label, sign + format_currency(amount), False, 6,
                            INK_2, INK)

    def settlement(self, net) -> None:
        self.set_y(max(self.get_y() + 12, SETTLEMENT_ANCHOR))
        top = self.get_y()
        height = 26.0

        self.set_fill_color(*HUESO)
        self.rect(MARGIN, top, CONTENT, height, style="F")

        self.set_fill_color(*MARCA)
        self.rect(MARGIN, top, 1.8, height, style="F")

        self.set_xy(MARGIN + 8, top + 4.5)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*INK_3)
        self.set_char_spacing(_tracking(0.09, 8))
        self.cell(0, 4, "NETO A PAGAR", new_x="LMARGIN", new_y="NEXT")
        self.set_char_spacing(0)

        self.set_xy(MARGIN + 8, top + 9.5)
        self.set_font("Helvetica", "B", 30)
        self.set_text_color(*NETO)
        self.set_char_spacing(_tracking(-0.04, 30))
        self.cell(0, 13, format_currency(net), new_x="LMARGIN", new_y="NEXT")
        self.set_char_spacing(0)

        self.set_y(top + height)

    def colophon(self, receipt: dict) -> None:
        self.set_y(-32)
        self.rule(RULE_SOFT)
        self.ln(4)

        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*INK_2)
        self.cell(0, 4.5, "Emitido el {} por {}".format(
            format_date(receipt["created_at"]), receipt["processed_by"]
        ), new_x="LMARGIN", new_y="NEXT")

        base = receipt.get("taxable_base")
        if base is not None:
            self.cell(0, 4.5, "Base gravable de ISR {}".format(
                format_currency(base)
            ), new_x="LMARGIN", new_y="NEXT")

        self.set_text_color(*INK_3)
        self.multi_cell(CONTENT * 0.78, 4.5, DISCLAIMER)


def _group(receipt: dict, kind: str) -> list:
    return [
        (item["description"], item["amount"])
        for item in receipt.get("items") or []
        if item["kind"] == kind
    ]


def _fallback_groups(receipt: dict) -> tuple:
    perceptions = [("Sueldo del periodo", receipt["gross_salary"])]
    deductions = [
        ("ISR retenido", receipt["isr_deduction"]),
        ("IMSS retenido", receipt["imss_deduction"]),
    ]
    return perceptions, deductions


def build_receipt_pdf(receipt: dict) -> bytes:
    perceptions = _group(receipt, "perception")
    deductions = _group(receipt, "deduction")
    if not perceptions and not deductions:
        perceptions, deductions = _fallback_groups(receipt)

    total_perceptions = sum(float(amount) for _, amount in perceptions)
    total_deductions = sum(float(amount) for _, amount in deductions)

    pdf = ReceiptPDF(format=PAGE_FORMAT)

    pdf.core_fonts_encoding = "cp1252"

    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    pdf.masthead("Recibo {}".format(receipt["id"]))
    pdf.identity(receipt)

    pdf.ln(11)
    pdf.rule(RULE)
    pdf.ln(7)
    pdf.ledger_group("Percepciones", total_perceptions, perceptions, False)

    pdf.ln(9)
    pdf.ledger_group("Deducciones", total_deductions, deductions, True)

    pdf.settlement(receipt["net_salary"])
    pdf.colophon(receipt)

    return bytes(pdf.output())


def receipt_filename(receipt: dict) -> str:
    start = receipt["period_start"]
    return "recibo-{}-{:04d}-{:02d}-{:02d}.pdf".format(
        receipt["id"], start.year, start.month, start.day
    )


def build_receipt_response_headers(receipt: dict) -> dict:
    return {
        "Content-Disposition": 'attachment; filename="{}"'.format(
            receipt_filename(receipt)
        )
    }
