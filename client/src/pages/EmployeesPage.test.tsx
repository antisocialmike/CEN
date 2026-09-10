import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import EmployeesPage from "./EmployeesPage";
import {
  activateEmployee,
  deactivateEmployee,
  listEmployees,
  resetEmployeePassword,
  updateEmployee
} from "../services/employeeService";

vi.mock("../services/employeeService", () => ({
  listEmployees: vi.fn(),
  updateEmployee: vi.fn(),
  deactivateEmployee: vi.fn(),
  activateEmployee: vi.fn(),
  resetEmployeePassword: vi.fn()
}));

const ana = {
  id: 3,
  name: "Ana Lopez",
  email: "ana@cen.com",
  role: "employee" as const,
  base_salary: 18000,
  is_active: true
};

const luis = {
  id: 4,
  name: "Luis Diaz",
  email: "luis@cen.com",
  role: "admin" as const,
  base_salary: 25000,
  is_active: false
};

const anaReset = {
  employee_id: 3,
  name: "Ana Lopez",
  email: "ana@cen.com",
  temporary_password: "Xk7mQ2pRt9Zc"
};

function renderPage() {
  return render(
    <MemoryRouter>
      <EmployeesPage />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  vi.mocked(listEmployees).mockResolvedValue([ana, luis]);
});

describe("listado", () => {
  it("muestra a cada persona con su correo y salario", async () => {
    renderPage();

    expect(await screen.findByText("Ana Lopez")).toBeInTheDocument();
    expect(screen.getByText(/ana@cen.com/)).toBeInTheDocument();
    expect(screen.getByText("Luis Diaz")).toBeInTheDocument();
  });

  it("marca a quien esta dado de baja y a los administradores", async () => {
    renderPage();

    expect(await screen.findByText("Dado de baja")).toBeInTheDocument();
    expect(screen.getByText("Administrador")).toBeInTheDocument();
  });

  it("avisa cuando la lista no carga", async () => {
    vi.mocked(listEmployees).mockRejectedValue(new Error("sin red"));

    renderPage();

    expect(await screen.findByText(/No se pudo cargar la lista/)).toBeInTheDocument();
  });

  it("invita a dar de alta cuando no hay nadie", async () => {
    vi.mocked(listEmployees).mockResolvedValue([]);

    renderPage();

    expect(await screen.findByText(/Todavía no hay nadie/)).toBeInTheDocument();
  });

  it("no ofrece restablecer ni dar de baja la propia cuenta", async () => {
    localStorage.setItem("cen_employee_id", "3");

    renderPage();

    expect(await screen.findByText("Ana Lopez")).toBeInTheDocument();
    expect(screen.getAllByText("Editar")).toHaveLength(2);
    expect(screen.getAllByText("Restablecer contraseña")).toHaveLength(1);
    expect(screen.queryByText("Dar de baja")).not.toBeInTheDocument();
  });
});

describe("edicion", () => {
  it("guarda los cambios y los refleja en la lista", async () => {
    vi.mocked(updateEmployee).mockResolvedValue({ ...ana, base_salary: 21000 });
    const user = userEvent.setup();
    renderPage();

    await user.click((await screen.findAllByText("Editar"))[0]);
    const salary = screen.getByLabelText(/Salario base mensual/);
    await user.clear(salary);
    await user.type(salary, "21000");
    await user.click(screen.getByText("Guardar cambios"));

    await waitFor(() => {
      expect(updateEmployee).toHaveBeenCalledWith(3, {
        name: "Ana Lopez",
        email: "ana@cen.com",
        role: "employee",
        baseSalary: 21000
      });
    });
    expect(await screen.findByText(/Se guardaron los cambios/)).toBeInTheDocument();
  });

  it("explica que el correo ya esta tomado", async () => {
    vi.mocked(updateEmployee).mockRejectedValue({ response: { status: 409 } });
    const user = userEvent.setup();
    renderPage();

    await user.click((await screen.findAllByText("Editar"))[0]);
    await user.click(screen.getByText("Guardar cambios"));

    expect(await screen.findByText(/Ese correo ya lo usa otra persona/)).toBeInTheDocument();
  });

  it("permite cancelar sin guardar", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click((await screen.findAllByText("Editar"))[0]);
    await user.click(screen.getByText("Cancelar"));

    expect(updateEmployee).not.toHaveBeenCalled();
    expect(screen.getAllByText("Editar")).toHaveLength(2);
  });
});

describe("restablecer contraseña", () => {
  it("pide confirmacion antes de invalidar la contraseña actual", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click((await screen.findAllByText("Restablecer contraseña"))[0]);

    expect(resetEmployeePassword).not.toHaveBeenCalled();
    expect(screen.getByText(/La contraseña actual de Ana Lopez dejará de funcionar/)).toBeInTheDocument();
    expect(screen.getByText("Restablecer")).toHaveFocus();
  });

  it("cancelar la confirmacion no restablece nada", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click((await screen.findAllByText("Restablecer contraseña"))[0]);
    await user.click(screen.getByText("Cancelar"));

    expect(resetEmployeePassword).not.toHaveBeenCalled();
    expect(screen.getAllByText("Restablecer contraseña")).toHaveLength(2);
  });

  it("muestra la contraseña temporal aparte y la enfoca", async () => {
    vi.mocked(resetEmployeePassword).mockResolvedValue(anaReset);
    const user = userEvent.setup();
    renderPage();

    await user.click((await screen.findAllByText("Restablecer contraseña"))[0]);
    await user.click(screen.getByText("Restablecer"));

    const panel = await screen.findByRole("region", { name: /Contraseña temporal de Ana Lopez/ });
    expect(resetEmployeePassword).toHaveBeenCalledWith(3);
    expect(screen.getByText("Xk7mQ2pRt9Zc")).toBeInTheDocument();
    expect(panel).toHaveFocus();
  });

  it("copia la contraseña al portapapeles", async () => {
    vi.mocked(resetEmployeePassword).mockResolvedValue(anaReset);
    const user = userEvent.setup();
    renderPage();

    await user.click((await screen.findAllByText("Restablecer contraseña"))[0]);
    await user.click(screen.getByText("Restablecer"));
    await user.click(await screen.findByText("Copiar"));

    expect(await screen.findByText("Copiada")).toBeInTheDocument();
    expect(await navigator.clipboard.readText()).toBe("Xk7mQ2pRt9Zc");
  });

  it("conserva la contraseña aunque se haga otra accion", async () => {
    vi.mocked(resetEmployeePassword).mockResolvedValue(anaReset);
    vi.mocked(deactivateEmployee).mockResolvedValue({ ...ana, is_active: false });
    const user = userEvent.setup();
    renderPage();

    await user.click((await screen.findAllByText("Restablecer contraseña"))[0]);
    await user.click(screen.getByText("Restablecer"));
    await screen.findByText("Xk7mQ2pRt9Zc");
    await user.click(screen.getByText("Dar de baja"));

    expect(await screen.findByText(/Sus recibos se conservan/)).toBeInTheDocument();
    expect(screen.getByText("Xk7mQ2pRt9Zc")).toBeInTheDocument();
  });

  it("la retira cuando se confirma que ya se compartio", async () => {
    vi.mocked(resetEmployeePassword).mockResolvedValue(anaReset);
    const user = userEvent.setup();
    renderPage();

    await user.click((await screen.findAllByText("Restablecer contraseña"))[0]);
    await user.click(screen.getByText("Restablecer"));
    await user.click(await screen.findByText("Ya la compartí"));

    await waitFor(() => expect(screen.queryByText("Xk7mQ2pRt9Zc")).not.toBeInTheDocument());
  });

  it("avisa si no se pudo restablecer", async () => {
    vi.mocked(resetEmployeePassword).mockRejectedValue(new Error("sin red"));
    const user = userEvent.setup();
    renderPage();

    await user.click((await screen.findAllByText("Restablecer contraseña"))[0]);
    await user.click(screen.getByText("Restablecer"));

    expect(await screen.findByText(/No se pudo restablecer la contraseña/)).toBeInTheDocument();
  });
});

describe("baja y reactivacion", () => {
  it("da de baja y avisa que los recibos se conservan", async () => {
    vi.mocked(deactivateEmployee).mockResolvedValue({ ...ana, is_active: false });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText("Dar de baja"));

    await waitFor(() => expect(deactivateEmployee).toHaveBeenCalledWith(3));
    expect(await screen.findByText(/Sus recibos se conservan/)).toBeInTheDocument();
  });

  it("reactiva a quien estaba dado de baja", async () => {
    vi.mocked(activateEmployee).mockResolvedValue({ ...luis, is_active: true });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText("Reactivar"));

    await waitFor(() => expect(activateEmployee).toHaveBeenCalledWith(4));
    expect(await screen.findByText(/vuelve a estar activa/)).toBeInTheDocument();
  });

  it("impide que el administrador se desactive a si mismo", async () => {
    vi.mocked(deactivateEmployee).mockRejectedValue({ response: { status: 400 } });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText("Dar de baja"));

    expect(
      await screen.findByText(/No puedes desactivar tu propia cuenta/)
    ).toBeInTheDocument();
  });
});
