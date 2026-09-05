import { NextResponse } from 'next/server'

// Base URL of the RecoverAI FastAPI backend.
// Configurable via env var; defaults to the local uvicorn address.
const API_URL = process.env.RECOVERAI_API_URL ?? 'http://127.0.0.1:8000'

export const dynamic = 'force-dynamic'

async function proxy(
  request: Request,
  path: string[],
  method: 'GET' | 'POST',
) {
  const endpoint = '/' + path.join('/')
  const target = `${API_URL}${endpoint}`

  try {
    const res = await fetch(target, {
      method,
      // The run-evaluation pipeline can take a while.
      signal: AbortSignal.timeout(method === 'POST' ? 300_000 : 15_000),
      cache: 'no-store',
      headers: { Accept: 'application/json' },
    })

    const text = await res.text()
    const data = text ? JSON.parse(text) : null

    if (!res.ok) {
      return NextResponse.json(
        { error: `Backend responded ${res.status}`, detail: data },
        { status: res.status },
      )
    }

    return NextResponse.json(data)
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json(
      {
        error: 'Could not reach the RecoverAI backend',
        detail: message,
        target,
      },
      { status: 502 },
    )
  }
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params
  return proxy(request, path, 'GET')
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params
  return proxy(request, path, 'POST')
}
