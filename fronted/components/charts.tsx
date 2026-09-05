'use client'

import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const AXIS = 'oklch(0.7 0.02 255)'
const GRID = 'oklch(1 0 0 / 8%)'

interface TooltipEntry {
  name?: string
  value?: number
  payload?: { fill?: string }
}

function ChartTooltip({
  active,
  payload,
  label,
  valueFormatter,
}: {
  active?: boolean
  payload?: TooltipEntry[]
  label?: string
  valueFormatter: (v: number) => string
}) {
  if (!active || !payload?.length) return null
  const entry = payload[0]
  return (
    <div className="rounded-md border border-border bg-popover px-3 py-2 text-sm shadow-lg">
      <p className="mb-0.5 font-medium text-popover-foreground">
        {label ?? entry.name}
      </p>
      <p className="font-mono tabular-nums text-muted-foreground">
        {valueFormatter(entry.value ?? 0)}
      </p>
    </div>
  )
}

export interface CategoryDatum {
  name: string
  value: number
  color: string
}

export function CategoryBarChart({
  data,
  valueFormatter,
}: {
  data: CategoryDatum[]
  valueFormatter: (v: number) => string
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 16, bottom: 4, left: 8 }}
      >
        <XAxis
          type="number"
          stroke={AXIS}
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: GRID }}
          tickFormatter={(v) => valueFormatter(Number(v))}
        />
        <YAxis
          type="category"
          dataKey="name"
          stroke={AXIS}
          fontSize={12}
          tickLine={false}
          axisLine={false}
          width={140}
        />
        <Tooltip
          cursor={{ fill: 'oklch(1 0 0 / 4%)' }}
          content={<ChartTooltip valueFormatter={valueFormatter} />}
        />
        <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={26}>
          {data.map((d) => (
            <Cell key={d.name} fill={d.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function OutcomeDonut({
  data,
  valueFormatter,
}: {
  data: CategoryDatum[]
  valueFormatter: (v: number) => string
}) {
  const total = data.reduce((sum, d) => sum + d.value, 0)
  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={70}
            outerRadius={100}
            paddingAngle={2}
            stroke="none"
          >
            {data.map((d) => (
              <Cell key={d.name} fill={d.color} />
            ))}
          </Pie>
          <Tooltip content={<ChartTooltip valueFormatter={valueFormatter} />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-3xl font-semibold tabular-nums text-foreground">
          {valueFormatter(total)}
        </span>
        <span className="text-xs uppercase tracking-wide text-muted-foreground">
          Total
        </span>
      </div>
    </div>
  )
}
