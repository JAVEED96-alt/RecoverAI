'use client'

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from '@/lib/utils'

function humanize(key: string) {
  return key
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

function renderValue(value: unknown) {
  if (value === null || value === undefined || value === '') {
    return <span className="text-muted-foreground/60">—</span>
  }
  if (typeof value === 'number') {
    return (
      <span className="font-mono tabular-nums">
        {new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(
          value,
        )}
      </span>
    )
  }
  return String(value)
}

interface DataTableProps {
  rows: Record<string, unknown>[]
  maxHeight?: string
  highlightColumn?: string
}

export function DataTable({
  rows,
  maxHeight = '22rem',
  highlightColumn,
}: DataTableProps) {
  if (!rows.length) return null

  const columns = Array.from(
    rows.reduce<Set<string>>((set, row) => {
      Object.keys(row).forEach((k) => set.add(k))
      return set
    }, new Set()),
  )

  return (
    <div
      className="overflow-auto rounded-lg border border-border"
      style={{ maxHeight }}
    >
      <Table>
        <TableHeader className="sticky top-0 z-10 bg-card">
          <TableRow className="hover:bg-transparent">
            {columns.map((col) => (
              <TableHead
                key={col}
                className="whitespace-nowrap text-xs font-medium uppercase tracking-wide text-muted-foreground"
              >
                {humanize(col)}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, i) => (
            <TableRow key={i} className="border-border/60">
              {columns.map((col) => (
                <TableCell
                  key={col}
                  className={cn(
                    'whitespace-nowrap text-sm',
                    highlightColumn === col && 'font-medium text-foreground',
                  )}
                >
                  {renderValue(row[col])}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
