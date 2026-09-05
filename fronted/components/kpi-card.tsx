import type { LucideIcon } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface KpiCardProps {
  label: string
  value: string
  icon: LucideIcon
  accent?: 'default' | 'positive' | 'warning' | 'negative'
  hint?: string
}

const accentMap: Record<
  NonNullable<KpiCardProps['accent']>,
  { icon: string; ring: string }
> = {
  default: { icon: 'text-muted-foreground', ring: 'bg-muted' },
  positive: { icon: 'text-[var(--chart-1)]', ring: 'bg-[var(--chart-1)]/12' },
  warning: { icon: 'text-[var(--chart-2)]', ring: 'bg-[var(--chart-2)]/12' },
  negative: { icon: 'text-[var(--chart-3)]', ring: 'bg-[var(--chart-3)]/12' },
}

export function KpiCard({
  label,
  value,
  icon: Icon,
  accent = 'default',
  hint,
}: KpiCardProps) {
  const styles = accentMap[accent]
  return (
    <Card className="flex flex-col gap-3 p-5">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">
          {label}
        </span>
        <span
          className={cn(
            'flex size-8 items-center justify-center rounded-md',
            styles.ring,
          )}
        >
          <Icon className={cn('size-4', styles.icon)} aria-hidden="true" />
        </span>
      </div>
      <div className="flex flex-col gap-0.5">
        <span className="font-mono text-2xl font-semibold tabular-nums tracking-tight text-foreground">
          {value}
        </span>
        {hint ? (
          <span className="text-xs text-muted-foreground">{hint}</span>
        ) : null}
      </div>
    </Card>
  )
}
