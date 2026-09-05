import { ArrowRight, Network } from 'lucide-react'
import { SectionCard } from '@/components/section-card'

const PIPELINE = [
  'Payment Data',
  'Detection',
  'Diagnosis',
  'Policy',
  'Execution',
  'Recovery Outcome',
  'Final Metrics',
]

export function ArchitectureSection() {
  return (
    <SectionCard
      title="RecoverAI Architecture"
      icon={Network}
      description="Each stage feeds the next — from raw payment failures to measured recovery."
    >
      <div className="flex flex-wrap items-center gap-2">
        {PIPELINE.map((stage, i) => (
          <div key={stage} className="flex items-center gap-2">
            <span className="rounded-md border border-border bg-muted/40 px-3 py-1.5 text-sm font-medium text-foreground">
              {stage}
            </span>
            {i < PIPELINE.length - 1 ? (
              <ArrowRight
                className="size-4 shrink-0 text-muted-foreground"
                aria-hidden="true"
              />
            ) : null}
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm text-muted-foreground">
        Serving layer:{' '}
        <span className="font-mono text-foreground">FastAPI</span>
        <ArrowRight
          className="mx-1.5 inline size-3.5 align-[-2px] text-muted-foreground"
          aria-hidden="true"
        />
        <span className="font-mono text-foreground">Next.js Dashboard</span>
      </p>
    </SectionCard>
  )
}
