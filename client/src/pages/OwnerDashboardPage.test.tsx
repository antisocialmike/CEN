import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import OwnerDashboardPage from "./OwnerDashboardPage";
import { getAnalytics, listOwnerCompanies, PayrollAnalytics } from "../services/ownerService";

vi.mock("../services/ownerService", async (importOriginal) => {
  const original = await importOriginal<typeof import("../services/ownerService")>();
  return { toAmount: original.toAmount, getAnalytics: vi.fn(), listOwnerCompanies: vi.fn() };
});

const companies = [
  {
    id: 1, legal_name: "Grupo Norte SA de CV", trade_name: "Norte", rfc: null,
    registro_patronal: null, entidad_federativa: null, is_active: true,
    created_at: "2026-01-01T00:00:00Z", active_employees: 3, risk_premium: null,
    admins: []
  },
  {
    id: 3, legal_name: "Servicios del Sur SC", trade_name: null, rfc: null,
    registro_patronal: null, entidad_federativa: null, is_active: false,
    created_at: "2026-01-01T00:00:00Z", active_employees: 1, risk_premium: null,
    admins: []
  }
];

function analytics(overrides: Partial<PayrollAnalytics> = {}): PayrollAnalytics {
  return {
    company_id: null,
    period: {
      start: "2025-10-01", end: "2026-09-24",
      previous_start: "2024-10-07", previous_end: "2025-09-30", periodicity: null
    },
    kpis: {
      gross_payroll: "30000.00", net_paid: "25500.00", isr_withheld: "3600.00",
      imss_withheld: "900.00", total_deductions: "4500.00", receipts: 2,
      paid_employees: 2, active_employees: 3, average_cost_per_employee: "15000.00",
      employer_cost: "6000.00", total_cost: "36000.00", employer_cost_pct: "20.0",
      change: {
        gross_payroll: "25.0", net_paid: "-3.5", isr_withheld: null,
        imss_withheld: "0.0", paid_employees: "0.0", average_cost_per_employee: "25.0",
        employer_cost: "25.0", total_cost: "25.0"
      }
    },
    monthly: [
      {
        month: "2026-08-01", gross_payroll: "10000.00", net_paid: "8500.00",
        isr_withheld: "1200.00", imss_withheld: "300.00", total_deductions: "1500.00", receipts: 1
      },
      {
        month: "2026-09-01", gross_payroll: "20000.00", net_paid: "17000.00",
        isr_withheld: "2400.00", imss_withheld: "600.00", total_deductions: "3000.00", receipts: 1
      }
    ],
    concepts: [
      {
        kind: "perception", concept: "sueldo", description: "Sueldo del periodo",
        amount: "30000.00", taxable: "30000.00", exempt: "0.00"
      },
      {
        kind: "deduction", concept: "isr", description: "ISR retenido",
        amount: "3600.00", taxable: "0.00", exempt: "0.00"
      }
    ],
    headcount: {
      active: 3, inactive: 1,
      by_month: [
        { month: "2026-08-01", hires: 0, terminations: 0 },
        { month: "2026-09-01", hires: 2, terminations: 1 }
      ]
    },
    top_salaries: [
      { id: 7, name: "Ana Gutiérrez", company_name: "Grupo Norte SA de CV", base_salary: "22000.00" }
    ],
    salary_histogram: [
      { label: "Hasta 10,000", min_salary: "0", max_salary: "10000", employees: 1 },
      { label: "20,000 a 35,000", min_salary: "20000", max_salary: "35000", employees: 2 }
    ],
    companies: [
      {
        id: 1, legal_name: "Grupo Norte SA de CV", is_active: true, gross_payroll: "25000.00",
        net_paid: "21000.00", employer_cost: "5000.00", total_cost: "30000.00", receipts: 1,
        paid_employees: 1, active_employees: 3
      },
      {
        id: 3, legal_name: "Servicios del Sur SC", is_active: false, gross_payroll: "5000.00",
        net_paid: "4500.00", employer_cost: "1000.00", total_cost: "6000.00", receipts: 1,
        paid_employees: 1, active_employees: 1
      }
    ],
    employer_cost: {
      coverage: { receipts_with_cost: 2, receipts_incomplete: 1, receipts_without_cost: 1 },
      components: [
        { group_key: "sar", component: "ceav", description: "Cesantía en edad avanzada y vejez", amount: "2000.00" },
        { group_key: "imss", component: "em_cuota_fija", description: "Enfermedad y maternidad, cuota fija", amount: "1500.00" }
      ],
      missing: [{ name: "isn", receipts: 2 }],
      monthly: [
        { month: "2026-08-01", imss: "0.00", sar: "0.00", infonavit: "0.00", isn: "0.00", covered_gross: "0.00" },
        { month: "2026-09-01", imss: "3000.00", sar: "2000.00", infonavit: "1000.00", isn: "0.00", covered_gross: "30000.00" }
      ]
    },
    ...overrides
  };
}

function LocationProbe() {
  const location = useLocation();
  return <p data-testid="ubicacion">{location.search}</p>;
}

function renderPage(initial = "/dueno") {
  return render(
    <MemoryRouter initialEntries={[initial]}>
      <Routes>
        <Route
          path="/dueno"
          element={
            <>
              <OwnerDashboardPage />
              <LocationProbe />
            </>
          }
        />
      </Routes>
    </MemoryRouter>
  );
}

async function kpi(label: string): Promise<HTMLElement> {
  const title = await screen.findByText(label, { selector: ".stat-card-label" });
  return title.closest(".kpi-card") as HTMLElement;
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(listOwnerCompanies).mockResolvedValue(companies);
  vi.mocked(getAnalytics).mockResolvedValue(analytics());
});

describe("indicadores", () => {
  it("muestra las cifras con su variación contra el periodo anterior", async () => {
    renderPage();

    const gross = await kpi("Nómina bruta");
    expect(within(gross).getByText("$30,000.00")).toBeInTheDocument();
    expect(within(gross).getByText(/\+25\.0 %/)).toBeInTheDocument();
    const net = await kpi("Neto pagado");
    expect(within(net).getByText(/-3\.5 %/)).toBeInTheDocument();
    const isr = await kpi("ISR retenido");
    expect(within(isr).getByText("Sin periodo previo")).toBeInTheDocument();
  });

  it("pide los últimos 12 meses de todas las empresas por omisión", async () => {
    renderPage();
    await kpi("Nómina bruta");

    const query = vi.mocked(getAnalytics).mock.calls[0][0];
    expect(query.companyId).toBe("all");
    expect(query.from).toMatch(/^\d{4}-\d{2}-01$/);
  });
});

describe("filtros", () => {
  it("elegir una empresa vuelve a pedir las cifras y la deja en la URL", async () => {
    const user = userEvent.setup();
    renderPage();
    await kpi("Nómina bruta");

    await user.selectOptions(screen.getByLabelText("Empresa"), "3");

    await waitFor(() => expect(getAnalytics).toHaveBeenLastCalledWith(
      expect.objectContaining({ companyId: 3 })
    ));
    expect(screen.getByTestId("ubicacion")).toHaveTextContent("empresa=3");
    expect(screen.getByRole("option", { name: "Servicios del Sur SC (inactiva)" })).toBeInTheDocument();
  });

  it("lee la empresa y el periodo de la URL", async () => {
    renderPage("/dueno?empresa=1&periodo=mes");
    await kpi("Nómina bruta");

    const query = vi.mocked(getAnalytics).mock.calls[0][0];
    expect(query.companyId).toBe(1);
    expect(screen.getByLabelText("Este mes")).toBeChecked();
  });

  it("cambiar el periodo vuelve a pedir las cifras", async () => {
    const user = userEvent.setup();
    renderPage();
    await kpi("Nómina bruta");

    await user.click(screen.getByLabelText("Este año"));

    await waitFor(() => expect(getAnalytics).toHaveBeenCalledTimes(2));
    expect(vi.mocked(getAnalytics).mock.calls[1][0].from).toMatch(/^\d{4}-01-01$/);
  });
});

describe("gráficas y tablas", () => {
  it("cada gráfica trae su tabla con las mismas cifras", async () => {
    renderPage();
    await screen.findByRole("heading", { name: "Nómina por mes" });

    const table = screen.getByRole("table", { name: "Nómina por mes" });
    expect(within(table).getByText("Septiembre de 2026")).toBeInTheDocument();
    expect(within(table).getByText("$17,000.00")).toBeInTheDocument();
  });

  it("compara empresas solo cuando hay más de una", async () => {
    renderPage();
    expect(
      await screen.findByRole("heading", { name: "Comparativo entre empresas" })
    ).toBeInTheDocument();
  });

  it("el comparativo suma el costo patronal de cada empresa", async () => {
    renderPage();
    const table = await screen.findByRole("table", { name: "Comparativo entre empresas" });
    const norte = within(table).getByRole("row", { name: /Grupo Norte/ });

    expect(within(norte).getAllByRole("cell").map((cell) => cell.textContent)).toEqual([
      "Grupo Norte SA de CV",
      "$25,000.00",
      "$5,000.00",
      "$30,000.00",
      "$21,000.00",
      "1",
      "3"
    ]);
  });

  it("muestra solo los meses con altas o bajas", async () => {
    renderPage();
    const table = await screen.findByRole("table", { name: "Altas y bajas por mes" });

    expect(within(table).getAllByRole("row")).toHaveLength(2);
    expect(within(table).getByText("Septiembre de 2026")).toBeInTheDocument();
  });

  it("recorre los meses de la tendencia con el teclado", async () => {
    const user = userEvent.setup();
    renderPage();
    const plot = await screen.findByRole("group", { name: /Percepciones y deducciones por mes/ });

    await user.click(plot);
    const tooltip = () => within(plot).getByRole("status");
    expect(tooltip()).toHaveTextContent(/sept?.? 26/);
    await user.keyboard("{ArrowLeft}");
    expect(tooltip()).toHaveTextContent(/ago.? 26/);
    expect(tooltip()).toHaveTextContent("$8,500.00");
  });
});

describe("costo patronal", () => {
  it("suma la nómina y el costo patronal en el costo total", async () => {
    renderPage();

    const total = await kpi("Costo total para la empresa");
    expect(within(total).getByText("$36,000.00")).toBeInTheDocument();
    const employer = await kpi("Costo patronal");
    expect(within(employer).getByText("20.0 % de la nómina")).toBeInTheDocument();
  });

  it("avisa qué recibos no tienen costo o les faltan parámetros", async () => {
    renderPage();
    const section = (await screen.findByRole("heading", { name: "Costo patronal" })).closest(
      "section"
    ) as HTMLElement;

    expect(within(section).getByText(/1 recibo del periodo se calcularon antes/)).toBeInTheDocument();
    expect(
      within(section).getByText(/2 recibos sin la tasa del impuesto sobre nóminas del estado/)
    ).toBeInTheDocument();
  });

  it("desglosa cada mes por grupo y lo repite en tabla", async () => {
    const user = userEvent.setup();
    renderPage();
    const columns = await screen.findByRole("list", { name: "Costo patronal por mes y por grupo" });

    const september = within(columns).getByLabelText(/sept?\.? 26: \$6,000\.00/);
    await user.hover(september);
    const tooltip = within(september.closest(".viz-stack") as HTMLElement).getByRole("status");
    expect(tooltip).toHaveTextContent("$3,000.00Cuotas IMSS");
    expect(tooltip).toHaveTextContent("20.0 %de la nómina");

    const table = screen.getByRole("table", { name: "Costo patronal por mes" });
    expect(within(table).getByText("$6,000.00")).toBeInTheDocument();
  });

  it("explica cuando todavía no hay recibos con costo patronal", async () => {
    vi.mocked(getAnalytics).mockResolvedValue(
      analytics({
        employer_cost: {
          coverage: { receipts_with_cost: 0, receipts_incomplete: 0, receipts_without_cost: 2 },
          components: [],
          missing: [],
          monthly: []
        }
      })
    );
    renderPage();

    expect(
      await screen.findByText(/Todavía no hay recibos con costo patronal/)
    ).toBeInTheDocument();
  });
});

describe("estados", () => {
  it("avisa cuando todavía no hay nómina", async () => {
    vi.mocked(getAnalytics).mockResolvedValue(
      analytics({
        kpis: { ...analytics().kpis, receipts: 0, active_employees: 0 },
        companies: []
      })
    );
    renderPage();

    expect(await screen.findByText("Todavía no hay nómina que mostrar")).toBeInTheDocument();
  });

  it("explica cuando las cifras no cargan", async () => {
    vi.mocked(getAnalytics).mockRejectedValue(new Error("red"));
    renderPage();

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudieron cargar las cifras");
  });
});
