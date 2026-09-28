import { useCallback, useEffect, useState } from "react";
import { Pagina, paginaQueExiste, POR_PAGINA } from "../services/pagina";
import { usePaginaEnUrl } from "./paginaEnUrl";

interface Cargada<T> {
  pagina: number;
  items: T[];
  total: number;
  porPagina: number;
}

export interface ListaPaginada<T> {
  // null mientras llega la pagina pedida: la pantalla enseña su esqueleto.
  items: T[] | null;
  total: number;
  // El tamano que uso el servidor, que puede recortar el pedido.
  porPagina: number;
  pagina: number;
  irAPagina: (pagina: number) => void;
  // La lista no se pudo traer; la pantalla decide que mensaje mostrar.
  fallo: boolean;
  // Cambia filas en su lugar (editar, dar de baja) sin volver a pedir la pagina.
  actualizar: (cambio: (items: T[]) => T[]) => void;
  // Vuelve a pedir la pagina actual, por ejemplo despues de dar de alta a alguien.
  recargar: () => void;
}

// `cargar` debe ser estable (una funcion del servicio, no una flecha nueva en cada render).
export function useListaPaginada<T>(
  cargar: (pagina: number) => Promise<Pagina<T>>
): ListaPaginada<T> {
  const [pagina, irA] = usePaginaEnUrl();
  const [cargada, setCargada] = useState<Cargada<T> | null>(null);
  const [fallo, setFallo] = useState(false);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let vigente = true;

    cargar(pagina)
      .then((resultado) => {
        if (!vigente) return;
        const existente = paginaQueExiste(resultado);
        if (existente !== null) {
          irA(existente, { reemplazar: true });
          return;
        }
        setCargada({
          pagina,
          items: resultado.items,
          total: resultado.total,
          porPagina: resultado.page_size
        });
        setFallo(false);
      })
      .catch(() => {
        if (!vigente) return;
        setCargada({ pagina, items: [], total: 0, porPagina: POR_PAGINA });
        setFallo(true);
      });

    return () => {
      vigente = false;
    };
  }, [cargar, pagina, version, irA]);

  const irAPagina = useCallback((nueva: number) => irA(nueva), [irA]);
  const actualizar = useCallback((cambio: (items: T[]) => T[]) => {
    setCargada((actual) => (actual ? { ...actual, items: cambio(actual.items) } : actual));
  }, []);
  const recargar = useCallback(() => setVersion((v) => v + 1), []);

  // Al recargar se sigue viendo la pagina de antes hasta que llega la nueva;
  // al cambiar de pagina, en cambio, no se enseñan filas de otra.
  const vigente = cargada !== null && cargada.pagina === pagina ? cargada : null;

  return {
    items: vigente?.items ?? null,
    total: vigente?.total ?? 0,
    porPagina: vigente?.porPagina ?? POR_PAGINA,
    pagina,
    irAPagina,
    fallo,
    actualizar,
    recargar
  };
}
