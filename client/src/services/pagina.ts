// Un tramo de una lista, tal como lo devuelve la API cuando se le pide `page`.
export interface Pagina<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export const POR_PAGINA = 20;

export function totalDePaginas(total: number, porPagina: number = POR_PAGINA): number {
  return Math.max(1, Math.ceil(total / porPagina));
}

// Una pagina que ya no existe (se borraron filas, o alguien escribio ?pagina=99)
// llega vacia pero con su total: se manda a la ultima que si tiene filas.
export function paginaQueExiste(pagina: Pagina<unknown>): number | null {
  const ultima = totalDePaginas(pagina.total, pagina.page_size);
  return pagina.items.length === 0 && pagina.page > ultima ? ultima : null;
}
