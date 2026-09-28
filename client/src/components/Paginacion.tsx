import { RefObject } from "react";
import { CaretLeft, CaretRight } from "@phosphor-icons/react";
import { formatInteger } from "../services/format";
import { POR_PAGINA, totalDePaginas } from "../services/pagina";

interface PaginacionProps {
  pagina: number;
  total: number;
  // Nombre del nav para lectores de pantalla: "Páginas de usuarios".
  etiqueta: string;
  alCambiar: (pagina: number) => void;
  porPagina?: number;
  // Inicio de la lista: si quedo arriba de la pantalla, se vuelve a el al cambiar.
  destino?: RefObject<HTMLElement | null>;
}

export default function Paginacion({
  pagina,
  total,
  etiqueta,
  alCambiar,
  porPagina = POR_PAGINA,
  destino
}: PaginacionProps) {
  // Una sola pagina no necesita controles.
  if (total <= porPagina) return null;

  const paginas = totalDePaginas(total, porPagina);
  const desde = (pagina - 1) * porPagina + 1;
  const hasta = Math.min(pagina * porPagina, total);

  function ir(nueva: number) {
    alCambiar(nueva);
    const inicio = destino?.current;
    if (inicio && inicio.getBoundingClientRect().top < 0) {
      inicio.scrollIntoView({ block: "start" });
    }
  }

  return (
    <nav className="paginacion" aria-label={etiqueta}>
      <p className="paginacion-rango">
        {formatInteger(desde)}–{formatInteger(hasta)} de {formatInteger(total)}
      </p>
      <div className="paginacion-controles">
        <button
          type="button"
          className="btn btn-line"
          onClick={() => ir(pagina - 1)}
          disabled={pagina <= 1}
        >
          <CaretLeft weight="bold" aria-hidden="true" />
          Anterior
        </button>
        <span className="paginacion-actual" aria-current="page">
          Página {pagina} de {paginas}
        </span>
        <button
          type="button"
          className="btn btn-line"
          onClick={() => ir(pagina + 1)}
          disabled={pagina >= paginas}
        >
          Siguiente
          <CaretRight weight="bold" aria-hidden="true" />
        </button>
      </div>
    </nav>
  );
}
