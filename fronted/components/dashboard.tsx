'use client'

import { useMemo, useState, type ReactNode } from 'react'
import useSWR from 'swr'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bot,
  CheckCircle2,
  CircleDollarSign,
  FileSearch,
  Layers,
  Loader2,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  Wallet,
  XCircle,
  Menu,
  X,
} from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { KpiCard } from '@/components/kpi-card'
import { SectionCard } from '@/components/section-card'
import { DataTable } from '@/components/data-table'
import {
  CategoryBarChart,
  OutcomeDonut,
  type CategoryDatum,
} from '@/components/charts'
import { ArchitectureSection } from '@/components/architecture-section'
import {
  explainPayment,
  formatINR,
  formatNumber,
  formatPercent,
  jsonFetcher,
  runEvaluation,
  type ExplanationResponse,
  type Metrics,
  type TableResponse,
} from '@/lib/recoverai'

const CHART = {
  emerald: 'oklch(0.76 0.15 162)',
  amber: 'oklch(0.82 0.14 78)',
  red: 'oklch(0.64 0.2 22)',
  blue: 'oklch(0.66 0.14 244)',
  slate: 'oklch(0.55 0.02 255)',
}

type View =
  | 'overview'
  | 'revenue'
  | 'policy'
  | 'audit'
  | 'exceptions'
  | 'lookup'
  | 'architecture'

const NAV = [
  { id: 'overview' as const, label: 'Overview', icon: BarChart3 },
  { id: 'revenue' as const, label: 'Revenue', icon: Wallet },
  { id: 'policy' as const, label: 'AI Policy', icon: Bot },
  { id: 'audit' as const, label: 'Recovery Audit', icon: FileSearch },
  { id: 'exceptions' as const, label: 'Exceptions', icon: AlertTriangle },
  { id: 'lookup' as const, label: 'Payment Lookup', icon: Search },
  { id: 'architecture' as const, label: 'Architecture', icon: Layers },
]

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex min-h-32 items-center justify-center rounded-xl border border-dashed border-border bg-muted/20 px-6 text-center text-sm text-muted-foreground">
      {message}
    </div>
  )
}

function PageHeading({
  title,
  description,
  icon: Icon,
}: {
  title: string
  description: string
  icon: typeof BarChart3
}) {
  return (
    <div className="mb-6 flex items-start gap-3">
      <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
        <Icon className="size-5 text-primary" />
      </span>
      <div>
        <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  )
}

function StatusBadge({
  status,
  children,
}: {
  status: 'success' | 'danger' | 'warning'
  children: ReactNode
}) {
  const styles = {
    success:
      'border-[var(--chart-2)]/30 bg-[var(--chart-2)]/10 text-[var(--chart-2)]',
    danger:
      'border-destructive/30 bg-destructive/8 text-destructive',
    warning:
      'border-[var(--chart-3)]/30 bg-[var(--chart-3)]/10 text-foreground',
  }

  return (
    <Badge variant="outline" className={styles[status]}>
      {children}
    </Badge>
  )
}

function ExplanationPanel({
  explanation,
}: {
  explanation: ExplanationResponse
}) {
  return (
    <div className="mt-5 rounded-2xl border border-primary/20 bg-primary/5 p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-xl bg-primary/10">
            <Sparkles className="size-5 text-primary" />
          </span>
          <div>
            <h3 className="font-semibold">Gemini Payment Explanation</h3>
            <p className="font-mono text-xs text-muted-foreground">
              {explanation.payment_id}
            </p>
          </div>
        </div>

        <Badge variant="outline" className="w-fit gap-1.5">
          <Sparkles className="size-3.5" />
          AI explanation ready
        </Badge>
      </div>

      <div className="mt-4 rounded-xl border border-border bg-card p-5">
        <pre className="whitespace-pre-wrap font-sans text-sm leading-7 text-foreground">
          {explanation.explanation}
        </pre>
      </div>

      <div className="mt-4 flex items-start gap-2 rounded-lg border border-border bg-background/60 px-3 py-2.5 text-xs text-muted-foreground">
        <ShieldCheck className="mt-0.5 size-3.5 shrink-0" />
        Gemini explains the recorded RecoverAI decision. It does not replace the
        detection, diagnosis, policy, execution, or recovery layers.
      </div>

      {explanation.case ? (
        <details className="mt-4">
          <summary className="cursor-pointer text-xs font-medium text-muted-foreground hover:text-foreground">
            View technical evidence
          </summary>
          <pre className="mt-3 max-h-80 overflow-auto rounded-xl border border-border bg-muted p-4 font-mono text-xs leading-5">
            {JSON.stringify(explanation.case, null, 2)}
          </pre>
        </details>
      ) : null}
    </div>
  )
}

export function Dashboard() {
  const [activeView, setActiveView] = useState<View>('overview')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [running, setRunning] = useState(false)
  const [lookupId, setLookupId] = useState('')
  const [explaining, setExplaining] = useState(false)
  const [explanation, setExplanation] =
    useState<ExplanationResponse | null>(null)
  const [explanationError, setExplanationError] =
    useState<string | null>(null)

  const metrics = useSWR<Metrics>('/metrics', jsonFetcher, {
    refreshInterval: 0,
  })
  const recovery = useSWR<TableResponse>('/recovery-outcomes', jsonFetcher)
  const exceptions = useSWR<TableResponse>('/exceptions', jsonFetcher)
  const policy = useSWR<TableResponse>('/policy-decisions', jsonFetcher)

  const connected = !metrics.error && metrics.data !== undefined
  const loading = metrics.isLoading && !metrics.data
  const m = metrics.data ?? {}

  const revenueData: CategoryDatum[] = useMemo(
    () => [
      {
        name: 'Revenue at Risk',
        value: Number(m.revenue_at_risk) || 0,
        color: CHART.amber,
      },
      {
        name: 'Revenue Recovered',
        value: Number(m.revenue_recovered) || 0,
        color: CHART.emerald,
      },
      {
        name: 'Revenue Unrecovered',
        value: Number(m.revenue_unrecovered) || 0,
        color: CHART.red,
      },
    ],
    [m.revenue_at_risk, m.revenue_recovered, m.revenue_unrecovered],
  )

  const outcomeData: CategoryDatum[] = useMemo(
    () => [
      {
        name: 'Successful',
        value: Number(m.successful_recoveries) || 0,
        color: CHART.emerald,
      },
      {
        name: 'Failed',
        value: Number(m.failed_recoveries) || 0,
        color: CHART.red,
      },
    ],
    [m.successful_recoveries, m.failed_recoveries],
  )

  const policyRows = policy.data?.data ?? []

  const policyActionData: CategoryDatum[] = useMemo(() => {
    const counts = new Map<string, number>()

    for (const row of policyRows) {
      const action = row.action != null ? String(row.action) : 'unknown'
      counts.set(action, (counts.get(action) ?? 0) + 1)
    }

    const palette = [
      CHART.emerald,
      CHART.blue,
      CHART.amber,
      CHART.slate,
      CHART.red,
    ]

    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([name, value], i) => ({
        name: name.replace(/_/g, ' '),
        value,
        color: palette[i % palette.length],
      }))
  }, [policyRows])

  async function handleRun() {
    setRunning(true)

    const t = toast.loading(
      'Running Detection → Diagnosis → Policy → Execution → Recovery → Metrics...',
    )

    try {
      await runEvaluation()

      toast.success('Recovery evaluation completed', { id: t })

      await Promise.all([
        metrics.mutate(),
        recovery.mutate(),
        exceptions.mutate(),
        policy.mutate(),
      ])
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Evaluation failed',
        { id: t },
      )
    } finally {
      setRunning(false)
    }
  }

  async function handleExplain(paymentId: string) {
    const id = paymentId.trim()

    if (!id) {
      setExplanationError('Enter a payment ID first.')
      return
    }

    setExplaining(true)
    setExplanation(null)
    setExplanationError(null)

    try {
      const result = await explainPayment(id)

      if (!result.found) {
        throw new Error('Payment was not found in RecoverAI data.')
      }

      setExplanation(result)
    } catch (err) {
      setExplanationError(
        err instanceof Error
          ? err.message
          : 'Unable to generate AI explanation.',
      )
    } finally {
      setExplaining(false)
    }
  }

  function navigate(view: View) {
    setActiveView(view)
    setMobileOpen(false)
    if (view !== 'lookup') {
      setExplanationError(null)
    }
  }

  function renderOverview() {
    return (
      <>
        <PageHeading
          title="Overview"
          description="Monitor revenue at risk, recovery performance, AI decisions, and exceptions."
          icon={BarChart3}
        />

        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            label="Revenue at Risk"
            value={formatINR(m.revenue_at_risk as number)}
            icon={Target}
            accent="warning"
          />
          <KpiCard
            label="Revenue Recovered"
            value={formatINR(m.revenue_recovered as number)}
            icon={TrendingUp}
            accent="positive"
          />
          <KpiCard
            label="Recovery Rate"
            value={formatPercent(m.recovery_rate_percent as number)}
            icon={CheckCircle2}
            accent="positive"
          />
          <KpiCard
            label="Exceptions"
            value={formatNumber(m.exception_count as number)}
            icon={AlertTriangle}
            accent="negative"
          />
        </section>

        <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
          <SectionCard
            title="Revenue Overview"
            icon={CircleDollarSign}
            description="At risk vs. recovered vs. unrecovered."
          >
            <CategoryBarChart
              data={revenueData}
              valueFormatter={formatINR}
            />
          </SectionCard>

          <SectionCard
            title="Recovery Outcomes"
            icon={Activity}
            description="Successful vs. failed recovery attempts."
          >
            <OutcomeDonut
              data={outcomeData}
              valueFormatter={formatNumber}
            />
          </SectionCard>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground">Records evaluated</p>
            <p className="mt-1 text-2xl font-semibold">
              {formatNumber(m.records_evaluated as number)}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground">Recovery attempts</p>
            <p className="mt-1 text-2xl font-semibold">
              {formatNumber(m.recovery_attempts as number)}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground">Successful</p>
            <p className="mt-1 text-2xl font-semibold text-[var(--chart-2)]">
              {formatNumber(m.successful_recoveries as number)}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground">Failed</p>
            <p className="mt-1 text-2xl font-semibold text-destructive">
              {formatNumber(m.failed_recoveries as number)}
            </p>
          </div>
        </div>

        {m.evaluation_type ? (
          <div className="mt-6 rounded-xl border border-[var(--chart-2)]/25 bg-[var(--chart-2)]/8 px-4 py-3 text-sm text-muted-foreground">
            Evaluation type:{' '}
            <span className="font-medium uppercase text-foreground">
              {String(m.evaluation_type)}
            </span>
            {' — '}
            recovery and revenue figures shown are synthetic evaluation results.
          </div>
        ) : null}
      </>
    )
  }

  function renderRevenue() {
    return (
      <>
        <PageHeading
          title="Revenue"
          description="Understand how much revenue is at risk and how much RecoverAI has recovered."
          icon={Wallet}
        />

        <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <KpiCard
            label="Revenue at Risk"
            value={formatINR(m.revenue_at_risk as number)}
            icon={Target}
            accent="warning"
          />
          <KpiCard
            label="Revenue Recovered"
            value={formatINR(m.revenue_recovered as number)}
            icon={TrendingUp}
            accent="positive"
          />
          <KpiCard
            label="Revenue Unrecovered"
            value={formatINR(m.revenue_unrecovered as number)}
            icon={XCircle}
            accent="negative"
          />
        </section>

        <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-[1.35fr_1fr]">
          <SectionCard
            title="Revenue Recovery Performance"
            icon={TrendingUp}
            description="Current evaluation result."
          >
            <CategoryBarChart
              data={revenueData}
              valueFormatter={formatINR}
            />
          </SectionCard>

          <SectionCard
            title="Recovery Rate"
            icon={CheckCircle2}
            description="Recovered attempts divided by total recovery attempts."
          >
            <div className="flex min-h-56 flex-col items-center justify-center">
              <div className="text-5xl font-bold tracking-tight text-primary">
                {formatPercent(m.recovery_rate_percent as number)}
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                {formatNumber(m.successful_recoveries as number)} successful of{' '}
                {formatNumber(m.recovery_attempts as number)} attempts
              </p>
            </div>
          </SectionCard>
        </div>
      </>
    )
  }

  function renderPolicy() {
    return (
      <>
        <PageHeading
          title="AI Policy"
          description="See how the recovery policy distributes actions across failed payments."
          icon={Bot}
        />

        <SectionCard
          title="Policy Action Distribution"
          icon={Bot}
          description="Actions selected by the RecoverAI policy layer."
        >
          {policyActionData.length ? (
            <>
              <CategoryBarChart
                data={policyActionData}
                valueFormatter={formatNumber}
              />

              <div className="mt-6">
                <DataTable rows={policyRows} highlightColumn="action" />
              </div>
            </>
          ) : (
            <EmptyState message="No policy decisions available yet. Run an evaluation to generate them." />
          )}
        </SectionCard>
      </>
    )
  }

  function renderAudit() {
    const rows = recovery.data?.data ?? []

    return (
      <>
        <PageHeading
          title="Recovery Audit"
          description="Inspect recovery outcomes and investigate individual payments with Gemini."
          icon={FileSearch}
        />

        <SectionCard
          title="Recovery Outcomes"
          icon={FileSearch}
          description="Full log of recovery outcomes per payment."
        >
          {rows.length ? (
            <>
              <DataTable rows={rows} highlightColumn="outcome" />

              <div className="mt-5 rounded-xl border border-border bg-muted/30 p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold">AI payment investigation</p>
                    <p className="text-xs text-muted-foreground">
                      Choose a payment and ask Gemini to explain the recorded case.
                    </p>
                  </div>
                  <Badge variant="outline" className="gap-1.5">
                    <Sparkles className="size-3.5" />
                    Gemini
                  </Badge>
                </div>

                <div className="flex flex-wrap gap-2">
                  {rows
                    .map((row) => row.payment_id)
                    .filter(Boolean)
                    .slice(0, 10)
                    .map((paymentId) => (
                      <Button
                        key={String(paymentId)}
                        variant="outline"
                        size="sm"
                        className="gap-2"
                        disabled={explaining}
                        onClick={() => handleExplain(String(paymentId))}
                      >
                        {explaining ? (
                          <Loader2 className="size-3.5 animate-spin" />
                        ) : (
                          <Sparkles className="size-3.5" />
                        )}
                        Explain {String(paymentId).slice(0, 14)}…
                      </Button>
                    ))}
                </div>
              </div>

              {explanationError ? (
                <div className="mt-4 rounded-xl border border-destructive/30 bg-destructive/8 p-4 text-sm text-destructive">
                  {explanationError}
                </div>
              ) : null}

              {explanation ? (
                <ExplanationPanel explanation={explanation} />
              ) : null}
            </>
          ) : (
            <EmptyState message="No recovery outcome records available." />
          )}
        </SectionCard>
      </>
    )
  }

  function renderExceptions() {
    const rows = exceptions.data?.data ?? []

    return (
      <>
        <PageHeading
          title="Exceptions"
          description="Review failed recovery records that require attention."
          icon={AlertTriangle}
        />

        <SectionCard
          title="Recovery Exceptions"
          icon={AlertTriangle}
          description="Cases that were not successfully recovered or require review."
          action={
            exceptions.data?.count ? (
              <StatusBadge status="danger">
                {exceptions.data.count} failed
              </StatusBadge>
            ) : null
          }
        >
          {rows.length ? (
            <DataTable rows={rows} highlightColumn="outcome" />
          ) : (
            <div className="flex items-center gap-2 rounded-xl border border-[var(--chart-2)]/25 bg-[var(--chart-2)]/8 px-4 py-4 text-sm text-[var(--chart-2)]">
              <CheckCircle2 className="size-4" />
              No recovery exceptions detected.
            </div>
          )}
        </SectionCard>
      </>
    )
  }

  function renderLookup() {
    return (
      <>
        <PageHeading
          title="Payment Lookup"
          description="Search a payment ID and get a complete AI-grounded investigation."
          icon={Search}
        />

        <SectionCard
          title="Investigate a Payment"
          icon={Search}
          description="Enter a payment ID from your Recovery Audit records."
        >
          <form
            className="flex flex-col gap-3 sm:flex-row"
            onSubmit={(event) => {
              event.preventDefault()
              handleExplain(lookupId)
            }}
          >
            <input
              value={lookupId}
              onChange={(event) => setLookupId(event.target.value)}
              placeholder="e.g. pay_198cc292508e4c"
              className="h-11 w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono outline-none transition focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 sm:flex-1"
            />
            <Button
              type="submit"
              disabled={explaining || !lookupId.trim()}
              className="h-11 gap-2 sm:min-w-40"
            >
              {explaining ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Sparkles className="size-4" />
              )}
              Explain with AI
            </Button>
          </form>

          {explanationError ? (
            <div className="mt-4 rounded-xl border border-destructive/30 bg-destructive/8 p-4 text-sm text-destructive">
              {explanationError}
            </div>
          ) : null}

          {explanation ? (
            <ExplanationPanel explanation={explanation} />
          ) : (
            <div className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-3">
              <div className="rounded-xl border border-border bg-muted/20 p-4">
                <Search className="size-5 text-primary" />
                <p className="mt-3 text-sm font-medium">Find the payment</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Use the payment ID from your recovery records.
                </p>
              </div>
              <div className="rounded-xl border border-border bg-muted/20 p-4">
                <Bot className="size-5 text-primary" />
                <p className="mt-3 text-sm font-medium">Explain the decision</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Gemini explains the stored diagnosis and policy action.
                </p>
              </div>
              <div className="rounded-xl border border-border bg-muted/20 p-4">
                <ShieldCheck className="size-5 text-primary" />
                <p className="mt-3 text-sm font-medium">Trace the outcome</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  See execution status and actual recovery outcome.
                </p>
              </div>
            </div>
          )}
        </SectionCard>
      </>
    )
  }

  function renderArchitecture() {
    return (
      <>
        <PageHeading
          title="Architecture"
          description="How RecoverAI moves a failed payment through detection, decision, action, and measurement."
          icon={Layers}
        />
        <ArchitectureSection />
      </>
    )
  }

  function renderView() {
    if (loading) {
      return (
        <div className="flex min-h-80 items-center justify-center">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Connecting to RecoverAI backend…
          </div>
        </div>
      )
    }

    switch (activeView) {
      case 'revenue':
        return renderRevenue()
      case 'policy':
        return renderPolicy()
      case 'audit':
        return renderAudit()
      case 'exceptions':
        return renderExceptions()
      case 'lookup':
        return renderLookup()
      case 'architecture':
        return renderArchitecture()
      default:
        return renderOverview()
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {mobileOpen ? (
        <button
          aria-label="Close navigation"
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      ) : null}

      <aside
        className={[
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-transform duration-200',
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        ].join(' ')}
      >
        <div className="flex h-20 items-center justify-between border-b border-sidebar-border px-5">
          <div className="flex items-center gap-3">
            <span className="flex size-9 items-center justify-center rounded-xl bg-sidebar-primary text-sidebar-primary-foreground">
              <CircleDollarSign className="size-5" />
            </span>
            <div>
              <p className="font-semibold tracking-tight">RecoverAI</p>
              <p className="text-xs text-sidebar-foreground/60">
                Revenue Recovery
              </p>
            </div>
          </div>

          <button
            className="rounded-lg p-1.5 hover:bg-sidebar-accent lg:hidden"
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
          >
            <X className="size-4" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-5">
          <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-sidebar-foreground/45">
            Console
          </p>

          {NAV.map((item) => {
            const Icon = item.icon
            const active = activeView === item.id

            return (
              <button
                key={item.id}
                onClick={() => navigate(item.id)}
                className={[
                  'flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition',
                  active
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground shadow-sm'
                    : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground',
                ].join(' ')}
              >
                <Icon className="size-4 shrink-0" />
                <span>{item.label}</span>
                {item.id === 'exceptions' && exceptions.data?.count ? (
                  <span className="ml-auto rounded-full bg-destructive/15 px-2 py-0.5 text-[10px] font-semibold text-red-300">
                    {exceptions.data.count}
                  </span>
                ) : null}
              </button>
            )
          })}
        </nav>

        <div className="border-t border-sidebar-border p-4">
          <div className="rounded-xl border border-sidebar-border bg-sidebar-accent/40 p-3">
            <div className="flex items-center gap-2">
              <span
                className={[
                  'size-2 rounded-full',
                  connected ? 'bg-[var(--chart-2)]' : 'bg-destructive',
                ].join(' ')}
              />
              <span className="text-xs font-medium">
                {connected ? 'Backend connected' : 'Backend offline'}
              </span>
            </div>
            <p className="mt-1 text-[10px] text-sidebar-foreground/50">
              FastAPI · RecoverAI pipeline
            </p>
          </div>
        </div>
      </aside>

      <main className="min-h-screen lg:pl-64">
        <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur">
          <div className="flex min-h-16 items-center justify-between gap-4 px-4 md:px-6">
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="icon"
                className="lg:hidden"
                onClick={() => setMobileOpen(true)}
                aria-label="Open navigation"
              >
                <Menu className="size-4" />
              </Button>

              <div className="hidden sm:block">
                <p className="text-sm font-semibold">
                  {NAV.find((item) => item.id === activeView)?.label}
                </p>
                <p className="text-xs text-muted-foreground">
                  AI Revenue Recovery Console
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {connected ? (
                <Badge
                  variant="outline"
                  className="gap-1.5 border-[var(--chart-2)]/30 bg-[var(--chart-2)]/8 text-[var(--chart-2)]"
                >
                  <span className="size-1.5 rounded-full bg-[var(--chart-2)]" />
                  Connected
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="gap-1.5 border-destructive/30 text-destructive"
                >
                  <span className="size-1.5 rounded-full bg-destructive" />
                  Offline
                </Badge>
              )}

              <Button
                onClick={handleRun}
                disabled={running || !connected}
                className="gap-2"
              >
                {running ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Activity className="size-4" />
                )}
                <span className="hidden sm:inline">
                  {running ? 'Running…' : 'Run Evaluation'}
                </span>
              </Button>
            </div>
          </div>
        </header>

        <div className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6 lg:px-8">
          <div className="mb-6 rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="flex size-8 items-center justify-center rounded-lg bg-primary/10">
                    <Sparkles className="size-4 text-primary" />
                  </span>
                  <span className="text-sm font-semibold">RecoverAI Controller</span>
                </div>
                <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
                  Detect failed payments, diagnose why they failed, choose a recovery
                  action, execute it, and measure the money actually recovered.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-lg bg-muted/60 px-3 py-2">
                  <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
                    Attempts
                  </p>
                  <p className="mt-1 font-semibold">
                    {formatNumber(m.recovery_attempts as number)}
                  </p>
                </div>
                <div className="rounded-lg bg-muted/60 px-3 py-2">
                  <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
                    Recovered
                  </p>
                  <p className="mt-1 font-semibold text-[var(--chart-2)]">
                    {formatPercent(m.recovery_rate_percent as number)}
                  </p>
                </div>
                <div className="rounded-lg bg-muted/60 px-3 py-2">
                  <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
                    Exceptions
                  </p>
                  <p className="mt-1 font-semibold">
                    {formatNumber(m.exception_count as number)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {connected ? (
            <div className="mb-6 grid grid-cols-2 gap-2 md:grid-cols-6">
              {[
                'Detection',
                'Diagnosis',
                'Policy',
                'Execution',
                'Recovery',
                'Metrics',
              ].map((step, index) => (
                <div
                  key={step}
                  className="flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2.5 shadow-sm"
                >
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary">
                    {index + 1}
                  </span>
                  <span className="text-xs font-medium">{step}</span>
                </div>
              ))}
            </div>
          ) : null}

          {renderView()}

          <footer className="mt-10 border-t border-border pt-5 text-xs text-muted-foreground">
            RecoverAI · AI Revenue Recovery Controller · FastAPI + Next.js ·
            Gemini-powered explanations
          </footer>
        </div>
      </main>
    </div>
  )
}
