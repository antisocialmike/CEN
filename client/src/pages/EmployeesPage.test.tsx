import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router-dom";
import EmployeesPage from "./EmployeesPage";
import {
  activateEmployee,
  deactivateEmployee,
  listEmployeesPage,
  resetEmployeePassword,
  updateEmployee
} from "../services/employeeService";

// Las etiquetas y isAssimilated son las de verdad; solo se simulan las llamadas.
vi.mock("../services/employeeService", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../services/employeeService")>()),
  listEmployeesPage: vi.fn(),
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
  is_active: true,
  tipo_regimen: "02" as const,
  tipo_jornada: "01" as const
};

const luis = {
  id: 4,
  name: "Luis Diaz",
  email: "luis@cen.com",
  role: "admin" as const,
  base_salary: 25000,
  is_active: false,
  tipo_regimen: "02" as const,
  tipo_jornada: "01" as const
};

const anaReset = {
  employee_id: 3,
  name: "Ana Lopez",
  email: "ana@cen.com",
  temporary_password: "Xk7mQ2pRt9Zc"
};

// Lo que devuelve la API al pedir una pagina.
function pagina<T>(items: T[], total = items.length, page = 1) {
  return { items, total, page, page_size: 20 };
}

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
  vi.mocked(listEmployeesPage).mockResolvedValue(pagina([ana, luis]));
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
    vi.mocked(listEmployeesPage).mockRejectedValue(new Error("sin red"));

    renderPage();

    expect(await screen.findByText(/No se pudo cargar la lista/)).toBeInTheDocument();
  });

  it("invita a dar de alta cuando no hay nadie", async () => {
    vi.mocked(listEmployeesPage).mockResolvedValue(pagina([]));

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

    expect(await screen.findByText(/Se guardarán cambios importantes/)).toBeInTheDocument();
    expect(updateEmployee).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() => {
      expect(updateEmployee).toHaveBeenCalledWith(3, {
        name: "Ana Lopez",
        email: "ana@cen.com",
        role: "employee",
        baseSalary: 21000,
        tipoRegimen: "02",
        tipoJornada: "01"
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

describe("administradores sin salario", () => {
  const pablo = {
    id: 8,
    name: "Pablo Soto",
    email: "pablo@cen.com",
    role: "admin" as const,
    base_salary: null,
    is_active: true,
    tipo_regimen: "02" as const,
    tipo_jornada: "01" as const
  };

  it("dice que no cobra nómina en vez de mostrar una cifra", async () => {
    vi.mocked(listEmployeesPage).mockResolvedValue(pagina([pablo]));
    renderPage();

    expect(await screen.findByText(/pablo@cen.com · Sin salario en nómina/)).toBeInTheDocument();
  });

  it("guarda sus cambios sin inventarle un salario", async () => {
    vi.mocked(listEmployeesPage).mockResolvedValue(pagina([pablo]));
    vi.mocked(updateEmployee).mockResolvedValue({ ...pablo, name: "Pablo Soto Ruiz" });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText("Editar"));
    expect(screen.getByLabelText(/Salario base mensual/)).toHaveValue(null);
    const name = screen.getByLabelText("Nombre completo");
    await user.clear(name);
    await user.type(name, "Pablo Soto Ruiz");
    await user.click(screen.getByText("Guardar cambios"));

    await waitFor(() => {
      expect(updateEmployee).toHaveBeenCalledWith(8, {
        name: "Pablo Soto Ruiz",
        email: "pablo@cen.com",
        role: "admin",
        baseSalary: null,
        tipoRegimen: "02",
        tipoJornada: "01"
      });
    });
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

    expect(await screen.findByText(/quedará fuera de la nómina/)).toBeInTheDocument();
    expect(deactivateEmployee).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Dar de baja" }));

    await waitFor(() => expect(deactivateEmployee).toHaveBeenCalledWith(3));
    expect(await screen.findByText(/quedó fuera de la nómina/)).toBeInTheDocument();
  });

  it("reactiva a quien estaba dado de baja", async () => {
    vi.mocked(activateEmployee).mockResolvedValue({ ...luis, is_active: true });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText("Reactivar"));

    expect(await screen.findByText(/volverá a estar activa/)).toBeInTheDocument();
    expect(activateEmployee).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Reactivar" }));

    await waitFor(() => expect(activateEmployee).toHaveBeenCalledWith(4));
    expect(await screen.findByText(/vuelve a estar activa/)).toBeInTheDocument();
  });

  it("impide que el administrador se desactive a si mismo", async () => {
    vi.mocked(deactivateEmployee).mockRejectedValue({ response: { status: 400 } });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText("Dar de baja"));
    await user.click(await screen.findByRole("button", { name: "Dar de baja" }));

    expect(
      await screen.findByText(/No puedes desactivar tu propia cuenta/)
    ).toBeInTheDocument();
  });
});

describe("paginacion", () => {
  function RutaActual() {
    const { search } = useLocation();
    return <output data-testid="busqueda">{search}</output>;
  }

  function renderEn(ruta: string) {
    return render(
      <MemoryRouter initialEntries={[ruta]}>
        <EmployeesPage />
        <RutaActual />
      </MemoryRouter>
    );
  }

  // 45 personas: tres paginas de 20, 20 y 5.
  function responderConTresPaginas() {
    vi.mocked(listEmployeesPage).mockImplementation(async (numero) =>
      numero <= 3
        ? pagina([{ ...ana, name: `Persona de la página ${numero}` }], 45, numero)
        : pagina([], 45, numero)
    );
  }

  it("con todo en una pagina no enseña controles", async () => {
    renderPage();

    await screen.findByText("Ana Lopez");
    expect(screen.queryByRole("navigation", { name: "Páginas de usuarios" })).toBeNull();
  });

  it("pide la siguiente pagina y la deja en la URL", async () => {
    responderConTresPaginas();
    const user = userEvent.setup();
    renderEn("/admin/usuarios");

    await screen.findByText("Persona de la página 1");
    await user.click(screen.getByRole("button", { name: /Siguiente/ }));

    expect(await screen.findByText("Persona de la página 2")).toBeInTheDocument();
    expect(listEmployeesPage).toHaveBeenLastCalledWith(2);
    expect(screen.getByTestId("busqueda")).toHaveTextContent("?pagina=2");
    expect(screen.getByRole("navigation", { name: "Páginas de usuarios" })).toHaveTextContent(
      "21–40 de 45"
    );
  });

  it("al recargar abre la pagina que dice la URL", async () => {
    responderConTresPaginas();
    renderEn("/admin/usuarios?pagina=3");

    expect(await screen.findByText("Persona de la página 3")).toBeInTheDocument();
    expect(listEmployeesPage).toHaveBeenCalledWith(3);
  });

  it("una pagina que ya no existe lleva a la ultima", async () => {
    responderConTresPaginas();
    renderEn("/admin/usuarios?pagina=9");

    expect(await screen.findByText("Persona de la página 3")).toBeInTheDocument();
    expect(screen.getByTestId("busqueda")).toHaveTextContent("?pagina=3");
  });

  it("una pagina que no es numero se lee como la primera", async () => {
    responderConTresPaginas();
    renderEn("/admin/usuarios?pagina=abc");

    expect(await screen.findByText("Persona de la página 1")).toBeInTheDocument();
    expect(listEmployeesPage).toHaveBeenCalledWith(1);
  });
});

describe("tipo de nomina y jornada", () => {
  const rosa = {
    id: 9,
    name: "Rosa Diaz",
    email: "rosa@cen.com",
    role: "employee" as const,
    base_salary: 15000,
    is_active: true,
    tipo_regimen: "09" as const,
    tipo_jornada: "01" as const
  };

  it("marca en la lista a quien cobra como asimilado", async () => {
    vi.mocked(listEmployeesPage).mockResolvedValue(pagina([ana, rosa]));
    renderPage();

    await screen.findByText("Rosa Diaz");
    expect(screen.getAllByText("Asimilado")).toHaveLength(1);
  });

  it("la jornada solo se pregunta a quien cobra sueldo", async () => {
    vi.mocked(listEmployeesPage).mockResolvedValue(pagina([ana]));
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText("Editar"));
    expect(screen.getByLabelText("Jornada")).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Tipo de nómina"), "09");
    expect(screen.queryByLabelText("Jornada")).not.toBeInTheDocument();
  });

  it("cambiar el tipo de nomina pide confirmacion y se guarda", async () => {
    vi.mocked(listEmployeesPage).mockResolvedValue(pagina([ana]));
    vi.mocked(updateEmployee).mockResolvedValue({ ...ana, tipo_regimen: "09" });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText("Editar"));
    await user.selectOptions(screen.getByLabelText("Tipo de nómina"), "09");
    await user.click(screen.getByText("Guardar cambios"));

    expect(await screen.findByText(/Se guardarán cambios importantes/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() => {
      expect(updateEmployee).toHaveBeenCalledWith(3, expect.objectContaining({
        tipoRegimen: "09"
      }));
    });
  });

  it("una jornada nocturna se guarda con su clave", async () => {
    vi.mocked(listEmployeesPage).mockResolvedValue(pagina([ana]));
    vi.mocked(updateEmployee).mockResolvedValue({ ...ana, tipo_jornada: "02" });
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText("Editar"));
    await user.selectOptions(screen.getByLabelText("Jornada"), "02");
    await user.click(screen.getByText("Guardar cambios"));

    await waitFor(() => {
      expect(updateEmployee).toHaveBeenCalledWith(3, expect.objectContaining({
        tipoJornada: "02"
      }));
    });
  });
});
