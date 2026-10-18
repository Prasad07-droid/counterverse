/**
 * src/api/client.ts
 * =================
 * Lightweight HTTP client for FastAPI backend with robust offline fallback.
 * Base URL configured via VITE_API_URL (default: empty = offline demo mode).
 * All requests enforce a 4-second timeout; any failure returns null.
 */

const DEFAULT_URL =
  typeof window !== 'undefined' && window.location && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : '';

const BASE_URL: string = (
  import.meta.env.VITE_API_URL !== undefined && import.meta.env.VITE_API_URL !== ''
    ? import.meta.env.VITE_API_URL
    : DEFAULT_URL
).replace(/\/+$/, '');
const TIMEOUT_MS = 4000;

export function isLiveApiConfigured(): boolean {
  return Boolean(BASE_URL);
}

async function fetchWithTimeout<T>(
  endpoint: string,
  options: RequestInit = {},
  customTimeoutMs?: number
): Promise<T | null> {
  if (!BASE_URL) {
    return null;
  }

  const controller = new AbortController();
  const timeoutMs = customTimeoutMs || TIMEOUT_MS;
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

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

/**
 * Call POST /api/v1/generate-report to obtain decision support report.
 */
export async function postReport(payload: { headline: string; oem?: string; engine?: string }): Promise<any | null> {
  return fetchWithTimeout<any>('/api/v1/generate-report', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Call GET /api/v1/live-news to scrape live supply chain news articles from Google News & GDELT.
 */
export async function getLiveScrapedNews(maxItems: number = 6): Promise<any | null> {
  return fetchWithTimeout<any>(
    `/api/v1/live-news?max_total=${maxItems}`,
    { method: 'GET' },
    8000 // 8s timeout for live web scraping
  );
}

/**
 * Call POST /api/v1/pcar/calculate to compute backend PCaR for an OEM.
 */
export async function postCalculatePcar(payload: {
  company: string;
  risk_score?: number;
  mc_samples?: number;
  custom_baseline_crore?: number;
}): Promise<any | null> {
  return fetchWithTimeout<any>('/api/v1/pcar/calculate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Call GET /api/v1/headlines to fetch 4-tier fallback live news feeds.
 */
export async function getHeadlines(maxRecords: number = 6): Promise<any | null> {
  return fetchWithTimeout<any>(`/api/v1/headlines?max_records=${maxRecords}`, {
    method: 'GET',
  });
}

/**
 * Call GET /api/v1/decision/events to fetch the ranked decision event queue.
 */
export async function getDecisionEvents(): Promise<any | null> {
  return fetchWithTimeout<any>('/api/v1/decision/events', {
    method: 'GET',
  });
}

/**
 * Call POST /api/v1/decision/action to execute workflow action (acknowledge, assign, comment, resolve).
 */
export async function postDecisionAction(payload: {
  event_id: string;
  action: 'acknowledge' | 'assign' | 'comment' | 'resolve';
  officer: string;
  notes?: string;
}): Promise<any | null> {
  return fetchWithTimeout<any>('/api/v1/decision/action', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}


