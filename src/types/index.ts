// Core Types for CounterVerse Enterprise Dashboard

export type NavView = 'war-room' | 'financial-exposure' | 'governance';

export type OEMKey = 'maruti' | 'hyundai' | 'tata' | 'mahindra' | 'macro';

export interface OEMProfile {
  id: OEMKey;
  name: string;
  marketShare: number;       // e.g. 0.417
  marketSharePct: number;    // e.g. 41.7
  dependencyRatio: number;   // e.g. 0.38
  dependencyRatioPct: number;// e.g. 38
  allocatedBaselineCr: number;// e.g. 21204
  description: string;
}

export type ExtractionEngine = 'fast' | 'slm';

export type Currency = 'INR' | 'USD' | 'EUR';

export interface CurrencyConfig {
  code: Currency;
  symbol: string;
  rateFromINR: number; // 1 INR in target currency
  name: string;
}

export type RouteStatus = 'optimal' | 'constrained' | 'starved' | 'blocked';

export interface SupplyChainNode {
  id: string;
  name: string;
  tier: string;
  tierCategory: 'port' | 'fab' | 'component' | 'assembly' | 'logistics' | 'retail';
  country: string;
  region: string;
  x: number;
  y: number;
  throughputPct: number;
  dependencyRatioPct: number;
  status: 'optimal' | 'constrained' | 'starved' | 'blocked';
  isChokePoint?: boolean;
}

export interface SupplyChainEdge {
  id: string;
  source: string;
  target: string;
  path: string; // SVG path
  midX: number;
  midY: number;
  flowPct: number;
  status: RouteStatus;
}

export interface IncidentData {
  headline: string;
  targetOEM: string;
  chokePoint: string;
  severityLevel: 'L1' | 'L2' | 'L3' | 'L4';
  severityPct: number;
  impactLabel: string;
  signalDate: string;
  country: string;
  component: string;
}

export interface DecisionRibbonState {
  tier1Signal: {
    event: string;
    level: string;
    choke: string;
    severityPct: number;
    region: string;
  };
  tier2Propagation: {
    nodesCount: number;
    conduitsCount: number;
    status: string;
  };
  tier3Stochastic: {
    meanDropPct: number;
    p95DropPct: number;
    description: string;
  };
  tier4Financial: {
    p95CostCr: number;
    targetOEM: string;
  };
}

export interface GroundingEntity {
  id: string;
  name: string;
  type: 'Chemical Precursor' | 'Commodity' | 'Integrated Circuit' | 'Supplier' | 'Manufacturing' | 'Automaker';
  hsCode: string;
  source: string;
  verified: boolean;
}

export interface ExposureIndexFactor {
  id: string;
  name: string;
  key: string;
  weight: number;
  score: number;
  contribution: number;
  source: string;
  status: 'Optimal' | 'Elevated' | 'Critical';
}

export interface BacktestScenario {
  metric: string;
  historicalValue: string;
  modelEstimate: string;
  deltaError: string;
  status: 'Calibrated' | 'Within Margin' | 'Deviated';
  details: string;
}

export interface ParsedBOM {
  fileName: string;
  fileSizeKb: number;
  isValid: boolean;
  componentCount: number;
  criticalComponents: number;
  calculatedPCaRCrores: number;
  parsedAt: string;
  errorMessage?: string;
}
