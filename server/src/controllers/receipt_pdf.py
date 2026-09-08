from fpdf import FPDF

COMPANY_NAME = "CEN Payroll"
COMPANY_SUBTITLE = "Sistema de nómina"
DISCLAIMER = (
    "Comprobante interno de nómina. No es un CFDI y no tiene validez fiscal "
    "ante el SAT."
)

MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

INK = (18, 20, 26)
MUTED = (110, 116, 128)
ACCENT = (35, 60, 200)
LINE = (214, 210, 202)


def format_currency(amount) -> str:
    return "$ {:,.2f}".format(float(amount))


def format_period(period) -> str:
    return "{} de {}".format(MONTHS[period.month - 1].capitalize(), period.year)


def format_date(moment) -> str:
    return "{} de {} de {}".format(
        moment.day, MONTHS[moment.month - 1], moment.year
    )


class ReceiptPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*INK)
        self.cell(0, 8, COMPANY_NAME, new_x="LMARGIN", new_y="NEXT")

        self.set_font("Helvetica", "", 9)
        self.set_text_color(*MUTED)
        self.cell(0, 5, COMPANY_SUBTITLE, new_x="LMARGIN", new_y="NEXT")

        self.set_draw_color(*LINE)
        self.line(self.l_margin, 32, self.w - self.r_margin, 32)
        self.ln(12)

    def footer(self) -> None:
        self.set_y(-22)
        self.set_draw_color(*LINE)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*MUTED)
        self.multi_cell(0, 4, DISCLAIMER)


def _field(pdf: ReceiptPDF, label: str, value: str, width: float) -> None:
    x, y = pdf.get_x(), pdf.get_y()

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*MUTED)
    pdf.cell(width, 4, label.upper(), new_x="LEFT", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*INK)
    pdf.cell(width, 6, value)

    pdf.set_xy(x + width, y)


def _amount_row(pdf: ReceiptPDF, label: str, amount, negative: bool = False) -> None:
    usable = pdf.w - pdf.l_margin - pdf.r_margin
    prefix = "- " if negative else ""

    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(*INK)
    pdf.cell(usable * 0.6, 8, label)
    pdf.cell(usable * 0.4, 8, prefix + format_currency(amount), align="R",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_draw_color(*LINE)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())


def build_receipt_pdf(receipt: dict) -> bytes:
    pdf = ReceiptPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=28)
    pdf.add_page()

    usable = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*INK)
    pdf.cell(0, 10, "Comprobante de nómina", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    _field(pdf, "Folio", "#{}".format(receipt["id"]), usable * 0.25)
    _field(pdf, "Periodo", format_period(receipt["period"]), usable * 0.4)
    _field(pdf, "Emitido el", format_date(receipt["created_at"]), usable * 0.35)
    pdf.ln(14)

    _field(pdf, "Empleado", str(receipt["employee_name"]), usable * 0.65)
    _field(pdf, "Correo", str(receipt["employee_email"]), usable * 0.35)
    pdf.ln(18)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 6, "PERCEPCIONES", new_x="LMARGIN", new_y="NEXT")
    _amount_row(pdf, "Salario bruto del periodo", receipt["gross_salary"])
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 6, "DEDUCCIONES", new_x="LMARGIN", new_y="NEXT")
    _amount_row(pdf, "ISR retenido", receipt["isr_deduction"], negative=True)
    _amount_row(pdf, "IMSS retenido", receipt["imss_deduction"], negative=True)
    pdf.ln(12)

    pdf.set_fill_color(244, 242, 238)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*INK)
    pdf.cell(usable * 0.6, 14, "  Neto a pagar", fill=True)
    pdf.cell(usable * 0.4, 14, format_currency(receipt["net_salary"]) + "  ",
             align="R", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 5, "Procesado por {}".format(receipt["processed_by"]))

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
