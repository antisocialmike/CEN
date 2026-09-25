import { KeyboardEvent, PointerEvent, useId, useState } from "react";
import { labelStride, niceTicks, scaleLinear } from "./scale";
import { useContainerWidth } from "./useContainerWidth";

export interface TrendSeries {
  name: string;
  // Un token de color (var(--viz-...)); nunca se usa para texto.
  color: string;
  kind: "area" | "line";
}

export interface TrendPoint {
  key: string;
  label: string;
  values: number[];
}

interface TrendChartProps {
  label: string;
  series: TrendSeries[];
  points: TrendPoint[];
  formatValue: (value: number) => string;
  formatTick: (value: number) => string;
  extraRows?: (point: TrendPoint) => { label: string; value: string }[];
}

const HEIGHT = 260;
const MARGIN = { top: 12, right: 16, bottom: 30, left: 72 };

export default function TrendChart({
  label,
  series,
  points,
  formatValue,
  formatTick,
  extraRows
}: TrendChartProps) {
  const [wrapRef, width] = useContainerWidth();
  const tooltipId = useId();
  const [active, setActive] = useState<number | null>(null);

  const innerWidth = Math.max(width - MARGIN.left - MARGIN.right, 1);
  const innerHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
  const max = Math.max(0, ...points.flatMap((point) => point.values));
  const ticks = niceTicks(max);
  const y = scaleLinear(ticks[ticks.length - 1], MARGIN.top + innerHeight, MARGIN.top);
  const step = points.length > 1 ? innerWidth / (points.length - 1) : 0;
  const x = (index: number) =>
    points.length > 1 ? MARGIN.left + index * step : MARGIN.left + innerWidth / 2;
  const stride = labelStride(points.length, innerWidth);
  const baseline = y(0);

  // Las etiquetas de las orillas se alinean hacia dentro para no salirse del SVG.
  function anchorFor(index: number): "start" | "middle" | "end" {
    if (points.length <= 1) return "middle";
    if (index === 0) return "start";
    return index === points.length - 1 ? "end" : "middle";
  }

  function pathFor(seriesIndex: number): string {
    return points
      .map((point, index) => `${index === 0 ? "M" : "L"}${x(index)},${y(point.values[seriesIndex])}`)
      .join(" ");
  }

  function nearest(clientX: number, rect: DOMRect): number {
    if (points.length <= 1) return 0;
    const offset = clientX - rect.left - MARGIN.left;
    return Math.min(points.length - 1, Math.max(0, Math.round(offset / step)));
  }

  function handlePointer(event: PointerEvent<SVGRectElement>) {
    const svg = event.currentTarget.ownerSVGElement;
    if (svg) setActive(nearest(event.clientX, svg.getBoundingClientRect()));
  }

  function handleKey(event: KeyboardEvent<HTMLDivElement>) {
    if (points.length === 0) return;
    const current = active ?? points.length - 1;
    if (event.key === "ArrowLeft") setActive(Math.max(0, current - 1));
    else if (event.key === "ArrowRight") setActive(Math.min(points.length - 1, current + 1));
    else if (event.key === "Home") setActive(0);
    else if (event.key === "End") setActive(points.length - 1);
    else return;
    event.preventDefault();
  }

  const activePoint = active === null ? null : points[active];
  const tooltipLeft = active === null ? 0 : Math.min(Math.max(x(active), 110), width - 110);

  return (
    <div className="viz-trend">
      <ul className="viz-legend" aria-hidden="true">
        {series.map((item) => (
          <li key={item.name}>
            <span
              className={item.kind === "area" ? "viz-key-rect" : "viz-key-line"}
              style={{ background: item.color }}
            />
            {item.name}
          </li>
        ))}
      </ul>

      <div
        ref={wrapRef}
        className="viz-trend-plot"
        tabIndex={0}
        role="group"
        aria-label={`${label}. Usa las flechas para recorrer los meses.`}
        aria-describedby={activePoint ? tooltipId : undefined}
        onKeyDown={handleKey}
        onFocus={() => setActive((current) => current ?? points.length - 1)}
        onBlur={() => setActive(null)}
      >
        <svg width={width} height={HEIGHT} aria-hidden="true">
          {ticks.map((tick) => (
            <g key={tick}>
              <line
                className="viz-grid"
                x1={MARGIN.left}
                x2={MARGIN.left + innerWidth}
                y1={y(tick)}
                y2={y(tick)}
              />
              <text className="viz-tick" x={MARGIN.left - 10} y={y(tick)} dy="0.32em" textAnchor="end">
                {formatTick(tick)}
              </text>
            </g>
          ))}

          {points.map((point, index) =>
            index % stride === 0 || index === points.length - 1 ? (
              <text
                key={point.key}
                className="viz-tick"
                x={x(index)}
                y={HEIGHT - 8}
                textAnchor={anchorFor(index)}
              >
                {point.label}
              </text>
            ) : null
          )}

          {points.length > 0 &&
            series.map((item, seriesIndex) => (
              <g key={item.name}>
                {item.kind === "area" && points.length > 1 && (
                  <path
                    d={`${pathFor(seriesIndex)} L${x(points.length - 1)},${baseline} L${x(0)},${baseline} Z`}
                    fill={item.color}
                    className="viz-area"
                  />
                )}
                <path d={pathFor(seriesIndex)} stroke={item.color} className="viz-line" />
                <circle
                  className="viz-dot"
                  cx={x(points.length - 1)}
                  cy={y(points[points.length - 1].values[seriesIndex])}
                  r={4}
                  fill={item.color}
                />
              </g>
            ))}

          {active !== null && activePoint && (
            <g>
              <line
                className="viz-crosshair"
                x1={x(active)}
                x2={x(active)}
                y1={MARGIN.top}
                y2={MARGIN.top + innerHeight}
              />
              {series.map((item, seriesIndex) => (
                <circle
                  key={item.name}
                  className="viz-dot"
                  cx={x(active)}
                  cy={y(activePoint.values[seriesIndex])}
                  r={5}
                  fill={item.color}
                />
              ))}
            </g>
          )}

          <rect
            x={MARGIN.left - step / 2}
            y={MARGIN.top}
            width={innerWidth + step}
            height={innerHeight}
            fill="transparent"
            onPointerMove={handlePointer}
            onPointerLeave={() => setActive(null)}
          />
        </svg>

        {activePoint && (
          <div
            id={tooltipId}
            className="viz-tooltip"
            role="status"
            style={{ left: tooltipLeft }}
          >
            <p className="viz-tooltip-title">{activePoint.label}</p>
            {series.map((item, seriesIndex) => (
              <p key={item.name} className="viz-tooltip-row">
                <span className="viz-key-line" style={{ background: item.color }} />
                <strong>{formatValue(activePoint.values[seriesIndex])}</strong>
                <span>{item.name}</span>
              </p>
            ))}
            {extraRows?.(activePoint).map((row) => (
              <p key={row.label} className="viz-tooltip-row is-extra">
                <span className="viz-key-line is-empty" />
                <strong>{row.value}</strong>
                <span>{row.label}</span>
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
