import { Currency, CurrencyConfig, OEMProfile } from '../types';
import { CURRENCY_CONFIGS } from '../data/mockData';

/**
 * Format Indian Rupee in Crores (1 Crore = 10,000,000)
 */
export function formatCurrencyValue(croresValue: number, currency: Currency = 'INR'): string {
  const config = CURRENCY_CONFIGS[currency] || CURRENCY_CONFIGS.INR;
  const converted = croresValue * config.rateFromINR;

  if (currency === 'INR') {
    // Standard Indian number grouping
    const rounded = Math.round(converted);
    const s = rounded.toString();
    if (s.length <= 3) return `${config.symbol}${s} Cr`;
    const last3 = s.slice(-3);
    const rest = s.slice(0, -3);
    let res = '';
    let temp = rest;
    while (temp.length > 2) {
      res = ',' + temp.slice(-2) + res;
      temp = temp.slice(0, -2);
    }
    return `${config.symbol}${(temp.length ? temp : '') + res + ',' + last3} Cr`;
  } else if (currency === 'USD') {
    // In USD millions
    return `${config.symbol}${converted.toFixed(1)}M`;
  } else {
    // In EUR millions
    return `${config.symbol}${converted.toFixed(1)}M`;
  }
}

export function formatPercentage(val: number, decimals: number = 1): string {
  return `${val.toFixed(decimals)}%`;
}

/**
 * Seeded Pseudo-Random Number Generator (Linear Congruential)
 * Guarantees exact determinism across simulation recalculations
 */
export class DeterministicRNG {
  private state: number;

  constructor(seed: number = 42) {
    this.state = seed % 2147483647;
    if (this.state <= 0) this.state += 2147483646;
  }

  next(): number {
    this.state = (this.state * 16807) % 2147483647;
    return (this.state - 1) / 2147483646;
  }

  nextNormal(mean: number, stdDev: number): number {
    // Box-Muller transform
    const u1 = Math.max(1e-10, this.next());
    const u2 = this.next();
    const randStdNormal = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
    return mean + stdDev * randStdNormal;
  }
}

export interface MonteCarloResult {
  samples: number[];
  meanDropPct: number;
  p95DropPct: number;
  p99DropPct: number;
  distributionBars: { binLabel: string; count: number; percentage: number; isP95: boolean; isP99: boolean }[];
  pcarCrores: number;
  meanLossCrores: number;
}

/**
 * Calculate deterministic Monte Carlo results
 */
export function simulateMonteCarlo(
  oem: OEMProfile,
  curtailmentPct: number,
  recoveryDays: number,
  substitutionPct: number,
  dependencyPct: number,
  sampleSize: number = 10000,
  seed: number = 42
): MonteCarloResult {
  const rng = new DeterministicRNG(seed);
  
  // Base drop influenced by curtailment and dependency, damped by substitution and recovery
  const netSeverity = (curtailmentPct / 100) * (dependencyPct / 100) * (1 - (substitutionPct / 100) * 0.45);
  const meanTarget = Math.max(5, Math.min(65, netSeverity * 45 + (recoveryDays / 90) * 8));
  const stdDevTarget = 6.8;

  const samples: number[] = [];
  for (let i = 0; i < Math.min(sampleSize, 5000); i++) {
    const draw = Math.max(0, Math.min(85, rng.nextNormal(meanTarget, stdDevTarget)));
    samples.push(draw);
  }

  samples.sort((a, b) => a - b);
  const mean = samples.reduce((acc, v) => acc + v, 0) / samples.length;
  const p95Index = Math.floor(samples.length * 0.95);
  const p99Index = Math.floor(samples.length * 0.99);
  const p95 = samples[p95Index] || mean * 1.4;
  const p99 = samples[p99Index] || mean * 1.6;

  // 18 histogram bins
  const binCount = 16;
  const maxVal = Math.min(80, Math.ceil(p99 * 1.2));
  const binWidth = maxVal / binCount;
  const bins: number[] = new Array(binCount).fill(0);

  samples.forEach((val) => {
    const idx = Math.min(binCount - 1, Math.floor(val / binWidth));
    bins[idx]++;
  });

  const distributionBars = bins.map((count, i) => {
    const rangeStart = (i * binWidth).toFixed(0);
    const rangeEnd = ((i + 1) * binWidth).toFixed(0);
    const binCenter = (i + 0.5) * binWidth;
    return {
      binLabel: `${rangeStart}-${rangeEnd}%`,
      count,
      percentage: (count / samples.length) * 100,
      isP95: binCenter >= p95 - binWidth / 2 && binCenter <= p95 + binWidth / 2,
      isP99: binCenter >= p99 - binWidth / 2 && binCenter <= p99 + binWidth / 2,
    };
  });

  // Calculate PCaR in Crores:
  // Allocated Baseline * (Drop% / 100) * Spot Premium multiplier (2.05x)
  const spotMultiplier = 2.05;
  const pcarCrores = Math.round(oem.allocatedBaselineCr * (p95 / 100) * spotMultiplier);
  const meanLossCrores = Math.round(oem.allocatedBaselineCr * (mean / 100) * 1.25);

  return {
    samples,
    meanDropPct: Number(mean.toFixed(1)),
    p95DropPct: Number(p95.toFixed(1)),
    p99DropPct: Number(p99.toFixed(1)),
    distributionBars,
    pcarCrores,
    meanLossCrores,
  };
}
