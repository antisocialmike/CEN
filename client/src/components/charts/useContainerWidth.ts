import { useCallback, useRef, useState } from "react";

// El SVG se dibuja al ancho real del contenedor para que el texto no se
// deforme. Se mide al montar, sin esperar al ResizeObserver: su primer aviso
// llega hasta que el navegador pinta, y mientras tanto la grafica saldria con
// el ancho de respaldo. Sin medida posible (jsdom) se queda el de respaldo.
export function useContainerWidth(fallback = 640) {
  const [width, setWidth] = useState(fallback);
  const observer = useRef<ResizeObserver | null>(null);

  const ref = useCallback((element: HTMLElement | null) => {
    observer.current?.disconnect();
    observer.current = null;
    if (!element) return;

    if (element.clientWidth > 0) setWidth(element.clientWidth);
    if (typeof ResizeObserver === "undefined") return;

    observer.current = new ResizeObserver(([entry]) => {
      const next = Math.round(entry.contentRect.width);
      if (next > 0) setWidth(next);
    });
    observer.current.observe(element);
  }, []);

  return [ref, width] as const;
}
