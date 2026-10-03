/**
 * src/api/client.ts
 * =================
 * Lightweight HTTP client for FastAPI backend with robust offline fallback.
 * Base URL configured via VITE_API_URL (default: empty = offline demo mode).
 * All requests enforce a 4-second timeout; any failure returns null.
 */

const BASE_URL: string = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');
const TIMEOUT_MS = 4000;

export function isLiveApiConfigured(): boolean {
  return Boolean(BASE_URL);
}

async function fetchWithTimeout<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T | null> {
  if (!BASE_URL) {
    return null;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const url = `${BASE_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as T;
  } catch (error) {
    clearTimeout(timeoutId);
    return null;
  }
}

/**
 * Call POST /api/v1/signal to extract structured disruption signal from text.
 */
export async function postSignal(
  headline: string,
  engine: string = 'fast'
): Promise<any | null> {
  return fetchWithTimeout<any>('/api/v1/signal', {
    method: 'POST',
    body: JSON.stringify({ headline, engine }),
  });
}

/**
 * Call POST /api/v1/simulate to run causal propagation and Monte Carlo draws.
 */
export async function postSimulate(
  signal: Record<string, any>
): Promise<any | null> {
  return fetchWithTimeout<any>('/api/v1/simulate', {
    method: 'POST',
    body: JSON.stringify(signal),
  });
}

/**
 * Call GET /api/v1/backtest/siam to retrieve dynamic SIAM 2021 backtest data.
 */
export async function getSiamBacktest(): Promise<any | null> {
  return fetchWithTimeout<any>('/api/v1/backtest/siam', {
    method: 'GET',
  });
}
