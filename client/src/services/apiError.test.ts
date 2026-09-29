import { describe, expect, it } from "vitest";
import { getErrorDetail, getValidationMessage } from "./apiError";

describe("getValidationMessage", () => {
  it("toma el mensaje de la primera validacion sin el prefijo de pydantic", () => {
    const error = {
      response: {
        status: 422,
        data: {
          detail: [
            { loc: ["body", "curp"], msg: "Value error, El digito verificador de la CURP no corresponde" }
          ]
        }
      }
    };

    expect(getValidationMessage(error)).toBe("El digito verificador de la CURP no corresponde");
  });

  it("no inventa nada si el detalle es texto", () => {
    expect(getValidationMessage({ response: { status: 400, data: { detail: "otra cosa" } } })).toBe(
      undefined
    );
  });
});

describe("getErrorDetail", () => {
  it("solo devuelve el detalle cuando es texto", () => {
    expect(getErrorDetail({ response: { status: 409, data: { detail: "Ya existe" } } })).toBe(
      "Ya existe"
    );
    expect(getErrorDetail({ response: { status: 422, data: { detail: [{ msg: "x" }] } } })).toBe(
      undefined
    );
  });
});
