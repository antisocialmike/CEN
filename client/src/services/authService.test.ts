import { beforeEach, describe, expect, it, vi } from "vitest";
import httpClient from "./httpClient";
import { changePassword } from "./authService";
import { getToken, mustChangePassword, saveSession } from "./authSession";

vi.mock("./httpClient", () => ({ default: { post: vi.fn() } }));

beforeEach(() => {
  localStorage.clear();
  vi.mocked(httpClient.post).mockReset();
  saveSession({
    accessToken: "token-viejo",
    role: "employee",
    name: "Ana",
    employeeId: 7,
    mustChangePassword: true
  });
});

describe("changePassword", () => {
  it("sigue la sesion con el token que devuelve la API", async () => {
    vi.mocked(httpClient.post).mockResolvedValueOnce({
      data: { access_token: "token-nuevo", token_type: "bearer" }
    });

    await changePassword("temporal123", "nuevaClave1");

    expect(httpClient.post).toHaveBeenCalledWith("/auth/password", {
      current_password: "temporal123",
      new_password: "nuevaClave1"
    });
    expect(getToken()).toBe("token-nuevo");
    expect(mustChangePassword()).toBe(false);
  });

  it("si la API lo rechaza, no toca la sesion", async () => {
    vi.mocked(httpClient.post).mockRejectedValueOnce({ response: { status: 400 } });

    await expect(changePassword("equivocada", "nuevaClave1")).rejects.toBeTruthy();

    expect(getToken()).toBe("token-viejo");
    expect(mustChangePassword()).toBe(true);
  });
});
