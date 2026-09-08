from fpdf import FPDF

COMPANY_NAME = "CEN Payroll"
DISCLAIMER = (
    "Comprobante interno de nómina. No es un CFDI y no tiene validez fiscal "
    "ante el SAT."
)

MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

INK = (20, 16, 14)
INK_SOFT = (90, 80, 73)
INK_FAINT = (128, 118, 109)
RULE = (207, 199, 188)
RULE_SOFT = (228, 222, 214)
ROSE = (177, 53, 76)

PAGE_FORMAT = "Letter"
PAGE_WIDTH = 215.9
PAGE_HEIGHT = 279.4
MARGIN = 24.0
CONTENT = PAGE_WIDTH - MARGIN * 2


def format_amount(amount) -> str:
    return "{:,.2f}".format(float(amount))


def format_currency(amount) -> str:
    return "${:,.2f}".format(float(amount))


def format_period(period) -> str:
    return "{} de {}".format(MONTHS[period.month - 1].capitalize(), period.year)


def format_date(moment) -> str:
    return "{} de {} de {}".format(
        moment.day, MONTHS[moment.month - 1], moment.year
    )


class ReceiptPDF(FPDF):
    def rule(self, color=RULE_SOFT, width=CONTENT) -> None:
        self.set_draw_color(*color)
        self.set_line_width(0.2)
        y = self.get_y()
        self.line(MARGIN, y, MARGIN + width, y)

    def masthead(self, folio: str) -> None:
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*INK)
        self.cell(CONTENT * 0.5, 6, COMPANY_NAME)

        self.set_font("Helvetica", "", 11)
        self.set_text_color(*INK_FAINT)
        self.cell(CONTENT * 0.5, 6, folio, align="R", new_x="LMARGIN",
                  new_y="NEXT")

        self.ln(3)
        self.rule(RULE)

    def identity(self, receipt: dict) -> None:
        self.ln(20)
        self.set_font("Times", "B", 34)
        self.set_text_color(*INK)
        self.cell(0, 14, format_period(receipt["period"]),
                  new_x="LMARGIN", new_y="NEXT")

        self.ln(5)
        self.set_font("Helvetica", "", 12.5)
        self.set_text_color(*INK)
        self.cell(0, 6.5, str(receipt["employee_name"]),
                  new_x="LMARGIN", new_y="NEXT")

        self.set_font("Helvetica", "", 10)
        self.set_text_color(*INK_FAINT)
        self.cell(0, 5, str(receipt["employee_email"]),
                  new_x="LMARGIN", new_y="NEXT")

    def ledger_group(self, title: str, total, items: list) -> None:
        self.set_font("Helvetica", "B", 11.5)
        self.set_text_color(*INK)
        self.cell(CONTENT * 0.62, 8, title)
        self.cell(CONTENT * 0.38, 8, format_amount(total), align="R",
                  new_x="LMARGIN", new_y="NEXT")
        self.rule()

        for label, amount in items:
            self.ln(1.5)
            self.set_font("Helvetica", "", 10.5)
            self.set_text_color(*INK_SOFT)
            self.set_x(MARGIN + 7)
            self.cell(CONTENT * 0.62 - 7, 6, label)
            self.set_text_color(*INK)
            self.cell(CONTENT * 0.38, 6, format_amount(amount), align="R",
                      new_x="LMARGIN", new_y="NEXT")

    def settlement(self, net) -> None:
        self.set_y(PAGE_HEIGHT - 88)
        self.rule(RULE)
        self.ln(12)
        top = self.get_y()

        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*INK_FAINT)
        self.set_x(MARGIN + 8)
        self.cell(0, 6, "Neto a pagar", new_x="LMARGIN", new_y="NEXT")

        self.ln(1)
        self.set_font("Times", "B", 44)
        self.set_text_color(*INK)
        self.set_x(MARGIN + 8)
        self.cell(0, 20, format_currency(net), new_x="LMARGIN", new_y="NEXT")

        self.set_draw_color(*ROSE)
        self.set_line_width(2.2)
        self.line(MARGIN + 1.1, top + 1.5, MARGIN + 1.1, self.get_y() - 3)
        self.set_line_width(0.2)

    def colophon(self, receipt: dict) -> None:
        self.set_y(-34)
        self.rule(RULE_SOFT)
        self.ln(4)

        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*INK_SOFT)
        self.cell(0, 4.5, "Emitido el {} por {}".format(
            format_date(receipt["created_at"]), receipt["processed_by"]
        ), new_x="LMARGIN", new_y="NEXT")

        self.set_text_color(*INK_FAINT)
        self.multi_cell(CONTENT * 0.78, 4.5, DISCLAIMER)


def build_receipt_pdf(receipt: dict) -> bytes:
    deductions = float(receipt["isr_deduction"]) + float(
        receipt["imss_deduction"]
    )

    pdf = ReceiptPDF(format=PAGE_FORMAT)
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    pdf.masthead("Comprobante {}".format(receipt["id"]))
    pdf.identity(receipt)

    pdf.ln(13)
    pdf.rule(RULE)
    pdf.ln(9)
    pdf.ledger_group(
        "Percepciones",
        receipt["gross_salary"],
        [("Salario bruto del periodo", receipt["gross_salary"])],
    )

    pdf.ln(12)
    pdf.ledger_group(
        "Deducciones",
        deductions,
        [
            ("ISR retenido", receipt["isr_deduction"]),
            ("IMSS retenido", receipt["imss_deduction"]),
        ],
    )

    pdf.settlement(receipt["net_salary"])
    pdf.colophon(receipt)

    return bytes(pdf.output())


def receipt_filename(receipt: dict) -> str:
    period = receipt["period"]
    return "recibo-{}-{:04d}-{:02d}.pdf".format(
        receipt["id"], period.year, period.month
    )


def build_receipt_response_headers(receipt: dict) -> dict:
    return {
        "Content-Disposition": 'attachment; filename="{}"'.format(
            receipt_filename(receipt)
        )
    }
