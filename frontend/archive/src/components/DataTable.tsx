/* ═══════════════════════════════════════════════════════════════════
   DataTable — Shared sortable data table component
   Extracted from ProseUISurfaceView and MissionControlSurface
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useMemo } from 'react'
import { Icon } from './Icon'

export interface TableColumn {
  key: string
  label: string
  sortable?: boolean
  render?: (value: any, row: any) => React.ReactNode
}

export interface TableRow {
  id: string
  [key: string]: any
}

interface DataTableProps {
  columns: TableColumn[]
  rows: TableRow[]
  onRowClick?: (row: TableRow) => void
  selectedId?: string | null
  defaultSortField?: string
  defaultSortDir?: 'asc' | 'desc'
}

const DataTable: React.FC<DataTableProps> = ({
  columns,
  rows,
  onRowClick,
  selectedId,
  defaultSortField,
  defaultSortDir = 'asc',
}) => {
  const [sortField, setSortField] = useState<string | null>(defaultSortField || null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(defaultSortDir)

  const handleSort = (key: string) => {
    if (sortField === key) {
      setSortDir(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(key)
      setSortDir('asc')
    }
  }

  const sortedRows = useMemo(() => {
    if (!sortField) return rows
    return [...rows].sort((a, b) => {
      const aVal = (a[sortField] ?? '').toString().toLowerCase()
      const bVal = (b[sortField] ?? '').toString().toLowerCase()
      const cmp = aVal.localeCompare(bVal)
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [rows, sortField, sortDir])

  return (
    <div className="data-table">
      <div className="table-header">
        {columns.map(col => (
          <span key={col.key}
                className={`table-th ${sortField === col.key ? 'sorted' : ''} ${col.sortable !== false ? 'table-th-sortable' : ''}`}
                onClick={() => col.sortable !== false && handleSort(col.key)}
                style={col.sortable !== false ? { cursor: 'pointer' } : undefined}>
            {col.label}
            {sortField === col.key && (
              <span className="sort-arrow">{sortDir === 'asc' ? ' ▲' : ' ▼'}</span>
            )}
          </span>
        ))}
      </div>
      {sortedRows.map(row => (
        <div key={row.id}
             className={`table-row ${selectedId === row.id ? 'selected' : ''}`}
             onClick={() => onRowClick?.(row)}>
          {columns.map(col => (
            <span key={col.key} className={`table-td ${col.key}`}>
              {col.render ? col.render(row[col.key], row) : row[col.key]}
            </span>
          ))}
        </div>
      ))}
    </div>
  )
}

export default DataTable
