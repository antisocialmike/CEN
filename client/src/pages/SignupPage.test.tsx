import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import SignupPage from "./SignupPage";
import { createEmployee } from "../services/employeeService";
import { currentDate } from "../services/format";

// Las etiquetas son las de verdad; solo se simula la llamada a la API.
vi.mock("../services/employeeService", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../services/employeeService")>()),
  createEmployee: vi.fn()
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <SignupPage />
    </MemoryRouter>
  );
}

async function llenar(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("Nombre completo"), "Rosa Diaz");
  await user.type(screen.getByLabelText("Correo"), "rosa@cen.com");
  await user.type(screen.getByLabelText(/Salario base mensual/), "15000");
  await user.type(screen.getByLabelText("Contraseña temporal"), "clave1234");
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(createEmployee).mockResolvedValue({
    id: 11,
    name: "Rosa Diaz",
    email: "rosa@cen.com",
    role: "employee",
    base_salary: 15000,
    is_active: true,
    tipo_regimen: "09",
    tipo_jornada: "01"
  });
});

describe("fecha de ingreso en el alta", () => {
  it("arranca en hoy y viaja al alta", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(screen.getByLabelText("Fecha de ingreso")).toHaveValue(currentDate());
    await llenar(user);
    await user.click(screen.getByRole("button", { name: "Dar de alta" }));

    await waitFor(() => {
      expect(createEmployee).toHaveBeenCalledWith(
        expect.objectContaining({ hireDate: currentDate() })
      );
    });
  });

  it("se puede dar de alta a alguien que entro antes", async () => {
    const user = userEvent.setup();
    renderPage();

    await llenar(user);
    fireEvent.change(screen.getByLabelText("Fecha de ingreso"), {
      target: { value: "2018-01-08" }
    });
    await user.click(screen.getByRole("button", { name: "Dar de alta" }));

    await waitFor(() => {
      expect(createEmployee).toHaveBeenCalledWith(
        expect.objectContaining({ hireDate: "2018-01-08" })
      );
    });
  });
});

describe("tipo de nomina en el alta", () => {
  it("por defecto es sueldos y salarios en jornada diurna", async () => {
    const user = userEvent.setup();
    renderPage();

    await llenar(user);
    await user.click(screen.getByRole("button", { name: "Dar de alta" }));

    await waitFor(() => {
      expect(createEmployee).toHaveBeenCalledWith(
        expect.objectContaining({ tipoRegimen: "02", tipoJornada: "01" })
      );
    });
  });

  it("a un asimilado no se le pregunta la jornada y se da de alta como 09", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.selectOptions(screen.getByLabelText("Tipo de nómina"), "09");
    expect(screen.queryByLabelText("Jornada")).not.toBeInTheDocument();
    expect(screen.getByText(/no cotiza al IMSS/)).toBeInTheDocument();

    await llenar(user);
    await user.click(screen.getByRole("button", { name: "Dar de alta" }));

    await waitFor(() => {
      expect(createEmployee).toHaveBeenCalledWith(
        expect.objectContaining({ tipoRegimen: "09" })
      );
    });
  });

  it("la jornada mixta se manda con su clave", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.selectOptions(screen.getByLabelText("Jornada"), "03");
    await llenar(user);
    await user.click(screen.getByRole("button", { name: "Dar de alta" }));

    await waitFor(() => {
      expect(createEmployee).toHaveBeenCalledWith(
        expect.objectContaining({ tipoRegimen: "02", tipoJornada: "03" })
      );
    });
  });
});
