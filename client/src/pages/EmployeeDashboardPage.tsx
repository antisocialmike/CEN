import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "motion/react";
import { blockVariants, stackVariants, useStill } from "../motion/variants";
import ErrorMessage from "../components/ErrorMessage";
import Paginacion from "../components/Paginacion";
import ReceiptCard from "../components/ReceiptCard";
import Skeleton from "../components/Skeleton";
import TrendChart, { TrendPoint } from "../components/charts/TrendChart";
import ChartTable from "../components/charts/ChartTable";
import { Receipt } from "@phosphor-icons/react";
import {
  getMyReceiptsPage,
  getMySummary,
  MySummary,
  PERIODICITY_LABELS,
  ReceiptPoint
} from "../services/payrollService";
import {
  formatCurrency,
  formatCurrencyCompact,
  formatDateShort,
  formatInteger,
  formatMonthShort,
  formatRange
} from "../services/format";
import { useListaPaginada } from "../routes/listaPaginada";
import "../styles/skin-dueno.css";

const NETO = "var(--viz-percepcion)";

// Un mes se nombra por el mes; una quincena o una semana, por el dia en que empieza.
function periodLabel(point: ReceiptPoint): string {
  return point.periodicity === "mensual"
    ? formatMonthShort(point.period_start)
    : formatDateShort(point.period_start);
}

export default function EmployeeDashboardPage() {
  const stackTravel = useStill(stackVariants);
  const blockTravel = useStill(blockVariants);
  const [summary, setSummary] = useState<MySummary | null>(null);
  const [summaryFailed, setSummaryFailed] = useState(false);
  const recibos = useListaPaginada(getMyReceiptsPage);
  const receipts = recibos.items;
  const inicioDeRecibos = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isMounted = true;

    getMySummary()
      .then((data) => isMounted && setSummary(data))
      .catch(() => isMounted && setSummaryFailed(true));

    return () => {
      isMounted = false;
    };
  }, []);

  const trendPoints = useMemo<TrendPoint[]>(
    () =>
      (summary?.recent ?? []).map((point) => ({
        key: String(point.id),
        label: periodLabel(point),
        values: [point.net_salary]
      })),
    [summary]
  );

  // Sin recibos no hay nada que resumir ni que listar: un solo aviso basta.
  const withoutReceipts =
    summary?.latest === null ||
    (receipts !== null && !recibos.fallo && recibos.total === 0);
  const latest = summary?.latest ?? null;
  const nextPeriod = summary?.next_period ?? null;
  const year = summary?.year_to_date;

  return (
    <div className="dashboard-panel">
      <div className="dashboard-panel-header">
        <div className="dashboard-panel-heading">
          <div>
            <h1>Mi nómina</h1>
            <p className="dashboard-panel-subtitle">
              Tu último pago, lo que llevas en el año y cada recibo con su salario bruto, lo que
              se retuvo por ISR e IMSS y el neto que recibiste.
            </p>
          </div>
        </div>
      </div>

      {withoutReceipts ? (
        <div className="empty-state">
          <span className="empty-state-icon" aria-hidden="true">
            <Receipt weight="bold" />
          </span>
          <p className="empty-state-title">Todavía no tienes recibos</p>
          <p>
            En cuanto tu administrador calcule tu nómina, el recibo aparecerá aquí con el
            desglose completo. No tienes que hacer nada.
          </p>
        </div>
      ) : (
        <>
          {summaryFailed && (
            <ErrorMessage message="No pudimos cargar tu resumen. Vuelve a intentarlo en unos minutos." />
          )}

          {summary === null && !summaryFailed && (
            <>
              <p className="visually-hidden" role="status">
                Cargando tu resumen
              </p>
              <div className="stat-row" aria-hidden="true">
                {[0, 1, 2].map((index) => (
                  <div className="stat-card" key={index}>
                    <Skeleton width="36px" height={36} />
                    <div className="skeleton-stack" style={{ flex: 1 }}>
                      <Skeleton width="70%" height={11} />
                      <Skeleton width="50%" height={16} />
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {latest && year && (
            <>
              <motion.div
                className="stat-row"
                variants={stackTravel}
                initial="initial"
                animate="animate"
              >
                <motion.div className="stat-card" variants={blockTravel}>
                  <div>
                    <p className="stat-card-label">Último neto recibido</p>
                    <p className="stat-card-value is-neto">{formatCurrency(latest.net_salary)}</p>
                    <p className="kpi-detail">
                      {formatRange(latest.period_start, latest.period_end)}
                    </p>
                  </div>
                </motion.div>
                {nextPeriod && (
                  <motion.div className="stat-card" variants={blockTravel}>
                    <div>
                      <p className="stat-card-label">Siguiente periodo (estimado)</p>
                      <p className="stat-card-value is-text">
                        {formatRange(nextPeriod.start, nextPeriod.end)}
                      </p>
                      <p className="kpi-detail">
                        {PERIODICITY_LABELS[nextPeriod.periodicity]}, como tu último recibo. La
                        fecha de pago la define tu empresa.
                      </p>
                    </div>
                  </motion.div>
                )}
                <motion.div className="stat-card" variants={blockTravel}>
                  <div>
                    <p className="stat-card-label">Neto recibido en {year.year}</p>
                    <p className="stat-card-value">{formatCurrency(year.net_paid)}</p>
                    <p className="kpi-detail">
                      {formatInteger(year.receipts)} {year.receipts === 1 ? "recibo" : "recibos"}
                    </p>
                  </div>
                </motion.div>
              </motion.div>

              <div className="section-title-row">
                <h2 className="section-title">Lo que llevas en {year.year}</h2>
                <p className="section-note">Por el inicio de cada periodo</p>
              </div>
              <div className="stat-row">
                <div className="stat-card">
                  <p className="stat-card-label">Bruto</p>
                  <p className="stat-card-value">{formatCurrency(year.gross_payroll)}</p>
                </div>
                <div className="stat-card">
                  <p className="stat-card-label">ISR retenido</p>
                  <p className="stat-card-value">{formatCurrency(year.isr_withheld)}</p>
                </div>
                <div className="stat-card">
                  <p className="stat-card-label">IMSS retenido</p>
                  <p className="stat-card-value">{formatCurrency(year.imss_withheld)}</p>
                </div>
              </div>

              <section className="owner-card" aria-labelledby="titulo-neto">
                <h2 id="titulo-neto">Tu neto por periodo</h2>
                <p className="owner-card-note">
                  {summary.recent.length === 1
                    ? "Tu único recibo hasta ahora."
                    : `Tus últimos ${formatInteger(summary.recent.length)} recibos.`}
                </p>
                <TrendChart
                  label="Neto recibido por periodo"
                  series={[{ name: "Neto", color: NETO, kind: "area" }]}
                  points={trendPoints}
                  formatValue={formatCurrency}
                  formatTick={formatCurrencyCompact}
                />
                <ChartTable
                  caption="Neto recibido por periodo"
                  columns={[{ label: "Periodo" }, { label: "Neto", numeric: true }]}
                  rows={summary.recent.map((point) => ({
                    key: point.id,
                    cells: [
                      formatRange(point.period_start, point.period_end),
                      formatCurrency(point.net_salary)
                    ]
                  }))}
                />
              </section>
            </>
          )}

          <div className="section-title-row" ref={inicioDeRecibos}>
            <h2 className="section-title">Historial</h2>
            <p className="section-note">Del más reciente al más antiguo</p>
          </div>

          {recibos.fallo && (
            <ErrorMessage message="No pudimos cargar tus recibos. Vuelve a intentarlo en unos minutos." />
          )}

          {receipts === null && (
            <>
              <p className="visually-hidden" role="status">
                Cargando tus recibos
              </p>
              <div className="receipt-list" aria-hidden="true">
                {[0, 1].map((index) => (
                  <div className="skeleton-card skeleton-stack" key={index}>
                    <Skeleton width="55%" height={18} />
                    <Skeleton height={14} />
                    <Skeleton height={14} />
                    <Skeleton height={14} />
                  </div>
                ))}
              </div>
            </>
          )}

          {receipts !== null && receipts.length > 0 && (
            <div className="receipt-list">
              {receipts.map((receipt) => (
                <ReceiptCard key={receipt.id} receipt={receipt} />
              ))}
            </div>
          )}

          <Paginacion
            pagina={recibos.pagina}
            total={recibos.total}
            porPagina={recibos.porPagina}
            etiqueta="Páginas de recibos"
            alCambiar={recibos.irAPagina}
            destino={inicioDeRecibos}
          />
        </>
      )}
    </div>
  );
}
