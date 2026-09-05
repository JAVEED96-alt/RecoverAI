export interface Metrics {
  records_evaluated?: number
  revenue_at_risk?: number
  revenue_recovered?: number
  revenue_unrecovered?: number
  recovery_rate_percent?: number
  recovery_attempts?: number
  successful_recoveries?: number
  failed_recoveries?: number
  exception_count?: number
  evaluation_type?: string
  [key: string]: unknown
}

export interface TableResponse {
  count: number
  data: Record<string, unknown>[]
}

const BASE = '/api/recoverai'

export async function jsonFetcher<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${BASE}${endpoint}`, { cache: 'no-store' })
  const body = await res.json()
  if (!res.ok) {
    throw new Error(body?.detail || body?.error || `Request failed (${res.status})`)
  }
  return body as T
}

export async function runEvaluation(): Promise<{ status: string; message: string }> {
  const res = await fetch(`${BASE}/run-evaluation`, { method: 'POST' })
  const body = await res.json()
  if (!res.ok) {
    throw new Error(
      typeof body?.detail === 'string'
        ? body.detail
        : body?.detail?.message || body?.error || 'Evaluation failed',
    )
  }
  return body
}

export function formatINR(value: number | undefined | null): string {
  const n = typeof value === 'number' && Number.isFinite(value) ? value : 0
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(n)
}

export function formatNumber(value: number | undefined | null): string {
  const n = typeof value === 'number' && Number.isFinite(value) ? value : 0
  return new Intl.NumberFormat('en-IN').format(n)
}

export function formatPercent(value: number | undefined | null): string {
  const n = typeof value === 'number' && Number.isFinite(value) ? value : 0
  return `${n.toFixed(2)}%`
}

export interface ExplanationResponse {
  payment_id: string
  found: boolean
  explanation: string
  case: Record<string, unknown> | null
}

export async function explainPayment(
  paymentId: string,
): Promise<ExplanationResponse> {
  return jsonFetcher<ExplanationResponse>(
    `/explain/${encodeURIComponent(paymentId)}`,
  )
}