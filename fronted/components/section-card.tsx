import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Card } from '@/components/ui/card'

interface SectionCardProps {
  title: string
  icon: LucideIcon
  description?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}

export function SectionCard({
  title,
  icon: Icon,
  description,
  action,
  children,
  className,
}: SectionCardProps) {
  return (
    <Card className={className}>
      <div className="flex items-start justify-between gap-4 px-6">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex size-9 items-center justify-center rounded-lg bg-primary/12">
            <Icon className="size-4.5 text-primary" aria-hidden="true" />
          </span>
          <div className="flex flex-col gap-0.5">
            <h2 className="text-base font-semibold text-foreground">{title}</h2>
            {description ? (
              <p className="text-sm text-muted-foreground text-pretty">
                {description}
              </p>
            ) : null}
          </div>
        </div>
        {action}
      </div>
      <div className="px-6">{children}</div>
    </Card>
  )
}
