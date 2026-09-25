interface ChartTableProps {
  caption: string;
  columns: { label: string; numeric?: boolean }[];
  rows: { key: string | number; cells: string[] }[];
}

// La vista en tabla de cada grafica: los mismos datos sin depender del color
// ni del puntero, para lectores de pantalla y para quien prefiera leer cifras.
export default function ChartTable({ caption, columns, rows }: ChartTableProps) {
  return (
    <details className="viz-table">
      <summary>Ver datos en tabla</summary>
      <div className="table-wrap">
        <table className="data-table">
          <caption className="visually-hidden">{caption}</caption>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.label} scope="col" className={column.numeric ? "num" : undefined}>
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.key}>
                {row.cells.map((cell, index) => (
                  <td key={index} className={columns[index]?.numeric ? "num" : undefined}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
