import { createContext, useContext } from "react";

export type OpcionesTunel = {
  // El elemento que disparo el salto: el logo del tunel nace ahi y no en medio de la pantalla.
  origen?: Element | null;
  // El origen ya es el logo: el del tunel lo continua visible desde el primer cuadro.
  compartido?: boolean;
};

export type PasarPorTunel = (navegar: () => void, opciones?: OpcionesTunel) => void;

// Sin proveedor (tests de una pagina suelta) se navega directo.
export const TunelContext = createContext<PasarPorTunel>((navegar) => navegar());

export function useTunel(): PasarPorTunel {
  return useContext(TunelContext);
}
