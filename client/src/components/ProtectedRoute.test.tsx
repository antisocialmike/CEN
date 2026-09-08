import { beforeEach, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import { saveSession } from "../services/authSession";

const adminSession = {
  accessToken: "token-abc",
  role: "admin" as const,
  name: "Ana Ramirez",
  employeeId: 7,
  mustChangePassword: false
};

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/login" element={<p>pantalla de login</p>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/cambiar-contrasena" element={<p>cambio de contrasena</p>} />
        </Route>
        <Route element={<ProtectedRoute allowedRole="admin" />}>
          <Route path="/admin" element={<p>panel de admin</p>} />
        </Route>
        <Route element={<ProtectedRoute allowedRole="employee" />}>
          <Route path="/empleado" element={<p>panel de empleado</p>} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  localStorage.clear();
});

describe("sin sesion", () => {
  it("manda al login", () => {
    renderAt("/admin");

    expect(screen.getByText("pantalla de login")).toBeInTheDocument();
  });
});

describe("con contrasena temporal", () => {
  beforeEach(() => {
    saveSession({ ...adminSession, mustChangePassword: true });
  });

  it("desvia cualquier ruta al cambio de contrasena", () => {
    renderAt("/admin");

    expect(screen.getByText("cambio de contrasena")).toBeInTheDocument();
  });

  it("deja entrar a la pantalla de cambio", () => {
    renderAt("/cambiar-contrasena");

    expect(screen.getByText("cambio de contrasena")).toBeInTheDocument();
  });
});

describe("con la contrasena ya definida", () => {
  it("deja pasar al panel de su rol", () => {
    saveSession(adminSession);

    renderAt("/admin");

    expect(screen.getByText("panel de admin")).toBeInTheDocument();
  });

  it("desvia al panel propio cuando el rol no coincide", () => {
    saveSession(adminSession);

    renderAt("/empleado");

    expect(screen.getByText("panel de admin")).toBeInTheDocument();
  });

  it("desvia al empleado fuera del panel de admin", () => {
    saveSession({ ...adminSession, role: "employee" });

    renderAt("/admin");

    expect(screen.getByText("panel de empleado")).toBeInTheDocument();
  });

  it("permite el cambio voluntario de contrasena", () => {
    saveSession(adminSession);

    renderAt("/cambiar-contrasena");

    expect(screen.getByText("cambio de contrasena")).toBeInTheDocument();
  });
});
