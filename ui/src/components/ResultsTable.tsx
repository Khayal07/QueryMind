import { useState } from 'react'

type ResultsTableProps = {
  columns: string[]
  rows: Record<string, unknown>[]
  rowCount?: number
}

const PAGE_SIZE = 25

function ResultsTable({ columns, rows, rowCount }: ResultsTableProps) {
  const [page, setPage] = useState(0)
  const totalPages = Math.ceil(rows.length / PAGE_SIZE)
  const pageRows = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const displayCount = rowCount ?? rows.length

  return (
    <div className="table-view-container">
      <div className="table-wrapper">
        <table className="result-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>
                  <span className="column-header">{col}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, idx) => (
              <tr key={idx} className={idx % 2 === 0 ? 'even' : 'odd'}>
                {columns.map((col) => (
                  <td key={`${idx}-${col}`} title={String(row[col] ?? '')}>
                    <span className="cell-value">{String(row[col] ?? '')}</span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="table-pagination">
          <button
            className="btn btn-ghost btn-sm"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            ← Prev
          </button>
          <span className="pagination-info">
            Page {page + 1} of {totalPages} • {displayCount} total rows
          </span>
          <button
            className="btn btn-ghost btn-sm"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}

export default ResultsTable
