import NumberFlow from "@number-flow/react";
import { Link } from "react-router-dom";
import { formatCurrency } from "../../services/format";

export interface Partida {
  concepto: string;
  importe: number;
  tipo: "percepcion" | "deduccion";
}

interface NetoDelPeriodoProps {
  neto: number;
  empleado: string;
  periodo: string;
  folio: string;
  partidas?: Partida[];
  variante?: "completa" | "compacta";
  href?: string;
  cargando?: boolean;
}

function Cifra({ valor, animar }: { valor: number; animar: boolean }) {
  const redondeado = Math.round(valor * 100) / 100;
  const entero = Math.trunc(redondeado);
  const centavos = Math.round(Math.abs(redondeado - entero) * 100);

  return (
    <span className="rv-neto-cifra">
      {animar ? (
        <NumberFlow
          value={entero}
          locales="es-MX"
          format={{ style: "currency", currency: "MXN", maximumFractionDigits: 0 }}
          aria-hidden="true"
        />
      ) : (
        <span aria-hidden="true">
          {new Intl.NumberFormat("es-MX", {
            style: "currency",
            currency: "MXN",
            maximumFractionDigits: 0
          }).format(entero)}
        </span>
      )}
      <span className="rv-neto-decimales" aria-hidden="true">
        .{String(centavos).padStart(2, "0")}
      </span>
      <span className="visually-hidden">{formatCurrency(valor)}</span>
    </span>
  );
}

function Esqueleto({ variante }: { variante: "completa" | "compacta" }) {
  return (
    <div className="rv-neto rv-neto--cargando" data-variante={variante} aria-busy="true">
      <span className="visually-hidden">Cargando el neto del periodo</span>
      <div className="rv-neto-cabecera" aria-hidden="true">
        <span className="rv-hueso rv-hueso--etiqueta" />
        <span className="rv-hueso rv-hueso--folio" />
      </div>
      <span className="rv-hueso rv-hueso--cifra" aria-hidden="true" />
      <span className="rv-hueso rv-hueso--contexto" aria-hidden="true" />
      {variante === "completa" && (
        <div className="rv-neto-desglose" aria-hidden="true">
          <span className="rv-hueso rv-hueso--fila" />
          <span className="rv-hueso rv-hueso--fila" />
          <span className="rv-hueso rv-hueso--fila" />
        </div>
      )}
    </div>
  );
}

export default function NetoDelPeriodo({
  neto,
  empleado,
  periodo,
  folio,
  partidas = [],
  variante = "completa",
  href,
  cargando = false
}: NetoDelPeriodoProps) {
  if (cargando) return <Esqueleto variante={variante} />;

  const contenido = (
    <>
      <div className="rv-neto-cabecera">
        <span className="rv-neto-etiqueta">Neto del periodo</span>
        <span className="rv-neto-folio">Folio {folio}</span>
      </div>

      <Cifra valor={neto} animar={variante === "completa"} />

      <p className="rv-neto-contexto">
        {empleado} · {periodo}
      </p>

      {variante === "completa" && partidas.length > 0 && (
        <dl className="rv-neto-desglose">
          {partidas.map((partida) => (
            <div className="rv-neto-fila" key={partida.concepto} data-tipo={partida.tipo}>
              <dt>
                <span className="rv-neto-punto" aria-hidden="true" />
                {partida.concepto}
              </dt>
              <dd>
                {partida.tipo === "deduccion" && <span aria-hidden="true">− </span>}
                {formatCurrency(Math.abs(partida.importe))}
                {partida.tipo === "deduccion" && (
                  <span className="visually-hidden"> retenido</span>
                )}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </>
  );

  if (href) {
    return (
      <Link
        className="rv-neto rv-neto--enlace"
        data-variante={variante}
        to={href}
        aria-label={`Recibo ${folio} de ${empleado}, ${periodo}. Neto ${formatCurrency(neto)}.`}
      >
        {contenido}
      </Link>
    );
  }

  return (
    <article className="rv-neto" data-variante={variante}>
      {contenido}
    </article>
  );
}
