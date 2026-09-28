import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";

const PARAMETRO = "pagina";

interface OpcionesDeCambio {
  // Para corregir una pagina que no existe: no deja un paso de mas en el historial.
  reemplazar?: boolean;
}

// La pagina vive en la URL (?pagina=2): sobrevive a recargar y el boton atras la regresa.
export function usePaginaEnUrl(): [number, (pagina: number, opciones?: OpcionesDeCambio) => void] {
  const [params, setParams] = useSearchParams();
  const leida = Number(params.get(PARAMETRO));
  const pagina = Number.isInteger(leida) && leida >= 1 ? leida : 1;

  const irA = useCallback(
    (nueva: number, opciones: OpcionesDeCambio = {}) => {
      setParams(
        (actuales) => {
          const siguientes = new URLSearchParams(actuales);
          if (nueva <= 1) {
            siguientes.delete(PARAMETRO);
          } else {
            siguientes.set(PARAMETRO, String(nueva));
          }
          return siguientes;
        },
        { replace: opciones.reemplazar ?? false }
      );
    },
    [setParams]
  );

  return [pagina, irA];
}
