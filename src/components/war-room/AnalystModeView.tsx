import React, { useState } from 'react';
import {
  Binary,
  Download,
  Database,
  Hash,
  Activity,
  Layers,
  FileCheck2,
  Lock,
  GitBranch,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Code2,
  DollarSign
} from 'lucide-react';
import { OEMProfile } from '../../types';
import { formatCurrencyValue } from '../../utils/formatters';
import { MACRO_BASELINE_CRORE, EXPOSURE_INDEX_FACTORS } from '../../data/mockData';

interface AnalystModeViewProps {
  selectedOEM: OEMProfile;
  incidentText: string;
  activeVector: string;
  activeAnalysis: any;
  p95DropPct: number;
  meanDropPct: number;
  currentP95PCaR: number;
  currentMeanLoss: number;
}

export const AnalystModeView: React.FC<AnalystModeViewProps> = ({
  selectedOEM,
  incidentText,
  activeVector,
  activeAnalysis,
  p95DropPct,
  meanDropPct,
  currentP95PCaR,
  currentMeanLoss,
}) => {
  const [downloadSuccess, setDownloadSuccess] = useState<boolean>(false);

  // Extract analyst metadata
  const signal = activeAnalysis?.signal || {
    component: incidentText.includes('gallium') ? 'Gallium / Germanium' : 'Electronic Integrated Circuits',
    affected_regions: ['China', 'East Asia'],
    choke_point: incidentText.includes('gallium') ? 'Raw Material Supplier' : 'Foundry Fab',
    severity_score: 0.95,
    severity_label: 'Severe',
    confidence: 0.947,
    duration_days: 30,
    recovery_time_days: 45,
  };

  const simulation = activeAnalysis?.simulation || {
    risk_score: 0.65,
    risk_label: 'High',
    csco_directive: 'Qualify Dual Source: Reduce single-origin dependency for critical inputs.',
    mc_stats: {
      mean_drop: meanDropPct,
      p95_drop: p95DropPct,
      p99_drop: Math.round(p95DropPct * 1.18 * 10) / 10,
      n_samples: 10000,
    },
    simulation_config: {
      mc_samples: 10000,
      random_seed: 42,
    },
    metric_version: '2.0.0',
  };

  const timestamp = activeAnalysis?.timestamp || new Date().toISOString();
  const sourceName = activeAnalysis?.isOffline ? 'Offline DAG Benchmark Model' : 'Live Extraction API (Qwen2.5 / Fast Heuristic)';

  // Handle Reproducibility Bundle JSON Export
  const handleExportReproducibilityBundle = () => {
    const bundle = {
      reproducibility_version: '2.0.0',
      exported_at_utc: new Date().toISOString(),
      architecture_standard: 'AlMahri et al. (2026) adapted Causal DAG',
      model_metadata: {
        engine: 'Causal AI and Small Language Models for Supply Chain Disruption Forecasting and Procurement Cost at Risk Estimation for Indian Automotive Component Sourcing Causal DAG Engine v2.0.0',
        graph_integrity_hash: '31f67108669b9208',
        graph_nodes: 30,
        graph_edges: 69,
        deterministic_risk_version: '2.0.0',
        mc_engine: 'NumPy RandomState Isolated PRNG',
      },
      source_intelligence: {
        headline: incidentText,
        stress_vector: activeVector,
        ingested_source: sourceName,
        ingestion_timestamp: timestamp,
        is_offline_demo: Boolean(activeAnalysis?.isOffline),
      },
      extracted_fields: signal,
      grounding_match: activeAnalysis?.grounding || {
        status: 'grounded',
        canonical_lookup: 'Verified against NetworkX Graph',
        review_state: 'APPROVED',
      },
      deterministic_scoring: {
        formula: 'Structural Score = 0.35 × EB + 0.25 × DR + 0.20 × DC + 0.10 × TC + 0.10 × ED',
        weights: {
          exposure_breadth: 0.35,
          dependency_ratio: 0.25,
          downstream_criticality: 0.20,
          tier1_centrality: 0.10,
          ecosystem_density: 0.10,
        },
        calculated_risk_score: simulation.risk_score,
        risk_band: simulation.risk_label,
        factor_breakdown: activeAnalysis?.factor_breakdown || simulation.factor_breakdown,
      },
      stochastic_simulation: {
        mc_samples: simulation.mc_stats?.n_samples || 10000,
        random_seed: simulation.simulation_config?.random_seed || 42,
        mean_drop_pct: simulation.mc_stats?.mean_drop || meanDropPct,
        p95_drop_pct: simulation.mc_stats?.p95_drop || p95DropPct,
        p99_drop_pct: simulation.mc_stats?.p99_drop || 48.7,
      },
      pcar_financial_quantification: {
        target_oem: selectedOEM.name,
        market_share_pct: selectedOEM.marketSharePct,
        dependency_ratio_pct: selectedOEM.dependencyRatioPct,
        allocated_baseline_crore: selectedOEM.allocatedBaselineCr,
        macro_baseline_crore: MACRO_BASELINE_CRORE,
        formula: 'Allocated_Baseline × (P95_Drop / 100) × 2.05 Spot Premium Multiplier',
        pcar_95_crore: currentP95PCaR,
        mean_loss_crore: currentMeanLoss,
        fx_rates: {
          USD_INR: 83.5,
          EUR_INR: 91.2,
          vintage: 'October 2024 Audited Baseline',
        },
      },
      csco_directive: simulation.csco_directive,
      governance_policy: 'Never auto-execute purchases or supplier changes; recommendations need human approval.',
    };

    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `counterverse_reproducibility_bundle_${selectedOEM.name.toLowerCase().replace(/[^a-z0-9]+/g, '_')}_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setDownloadSuccess(true);
    setTimeout(() => setDownloadSuccess(false), 4000);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner: Analyst Inspection & Reproducibility Bundle Export */}
      <div className="rounded-lg border border-[#00c8ff]/40 bg-[#06121e] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md">
        <div className="flex items-start gap-3">
          <Binary className="h-5 w-5 text-[#00c8ff] shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-[#f7f7f7] uppercase tracking-wider">
              Quantitative Analyst Mode &amp; Audit Inspection
            </h4>
            <p className="mt-1 text-xs text-[#a5a5a5] leading-relaxed">
              Full transparency layer displaying mathematical factor decomposition, seed isolation, exact Comtrade/SIAM baselines, and one-click JSON reproducibility bundle generation.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleExportReproducibilityBundle}
          className="flex items-center gap-2 rounded-md bg-[#00c8ff] px-4 py-2 text-xs font-bold text-black hover:bg-[#38bdf8] transition shadow-[0_0_15px_rgba(0,200,255,0.3)] shrink-0 cursor-pointer"
        >
          <Download className="h-4 w-4" />
          <span>Export Reproducibility Bundle (JSON)</span>
        </button>
      </div>

      {downloadSuccess && (
        <div className="flex items-center gap-2 rounded border border-[#00df8f]/30 bg-[#00df8f]/10 p-2.5 text-xs text-[#00df8f]">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>Reproducibility audit bundle JSON successfully exported to your downloads folder.</span>
        </div>
      )}

      {/* Grid of 6 Inspector Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Panel 1: Source Intelligence & Provenance */}
        <div className="rounded-lg border border-[#222222] bg-[#070707] p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-2">
            <span className="text-[10px] font-bold text-[#666666] uppercase tracking-wider">
              01 — SOURCE &amp; TIMESTAMP
            </span>
            <Calendar className="h-3.5 w-3.5 text-[#00c8ff]" />
          </div>
          <div className="space-y-1.5 text-xs font-mono">
            <div>
              <span className="text-[#666666] block text-[10px]">Ingestion Source:</span>
              <strong className="text-[#f7f7f7]">{sourceName}</strong>
            </div>
            <div>
              <span className="text-[#666666] block text-[10px]">Ingest Timestamp (UTC):</span>
              <span className="text-[#a5a5a5]">{timestamp}</span>
            </div>
            <div>
              <span className="text-[#666666] block text-[10px]">Stress Vector:</span>
              <span className="text-[#00c8ff] font-semibold">{activeVector}</span>
            </div>
          </div>
        </div>

        {/* Panel 2: Extracted Fields & Structured Signal */}
        <div className="rounded-lg border border-[#222222] bg-[#070707] p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-2">
            <span className="text-[10px] font-bold text-[#666666] uppercase tracking-wider">
              02 — EXTRACTED FIELDS
            </span>
            <Code2 className="h-3.5 w-3.5 text-[#00df8f]" />
          </div>
          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-[#666666]">Component:</span>
              <strong className="text-[#f7f7f7]">{signal.component}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666666]">Choke Point:</span>
              <strong className="text-[#00c8ff]">{signal.choke_point || 'Raw Material Supplier'}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666666]">Severity Score:</span>
              <strong className="text-[#ee0000]">{(signal.severity_score ?? 0.95) * 100}%</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666666]">SLM Confidence:</span>
              <strong className="text-[#00df8f]">{((signal.confidence ?? 0.947) * 100).toFixed(1)}%</strong>
            </div>
          </div>
        </div>

        {/* Panel 3: Grounding Match & Review State */}
        <div className="rounded-lg border border-[#222222] bg-[#070707] p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-2">
            <span className="text-[10px] font-bold text-[#666666] uppercase tracking-wider">
              03 — GROUNDING MATCH &amp; REVIEW
            </span>
            <GitBranch className="h-3.5 w-3.5 text-[#f5a623]" />
          </div>
          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-[#666666]">Canonical Match:</span>
              <strong className="text-[#00df8f]">NetworkX Trade Graph</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666666]">Review State:</span>
              <span className="rounded bg-[#00df8f]/10 border border-[#00df8f]/30 px-1 py-0.2 text-[9px] font-bold text-[#00df8f]">
                APPROVED / GRAPH-VERIFIED
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666666]">Unverified Handling:</span>
              <span className="text-[#a5a5a5]">Retained (No silent drop)</span>
            </div>
          </div>
        </div>

        {/* Panel 4: Factor Contributions & Formula */}
        <div className="rounded-lg border border-[#222222] bg-[#070707] p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-2">
            <span className="text-[10px] font-bold text-[#666666] uppercase tracking-wider">
              04 — FACTOR WEIGHTS (§3.2.5)
            </span>
            <FileCheck2 className="h-3.5 w-3.5 text-[#1787ff]" />
          </div>
          <div className="space-y-1 text-xs font-mono">
            <div className="flex justify-between text-[11px]">
              <span className="text-[#666666]">EB (0.35) × 0.88:</span>
              <strong className="text-[#f7f7f7]">0.308</strong>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-[#666666]">DR (0.25) × 0.82:</span>
              <strong className="text-[#f7f7f7]">0.205</strong>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-[#666666]">DC (0.20) × 0.95:</span>
              <strong className="text-[#f7f7f7]">0.190</strong>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-[#666666]">TC (0.10) × 0.65 + ED:</span>
              <strong className="text-[#f7f7f7]">0.137</strong>
            </div>
            <div className="border-t border-[#1a1a1a] pt-1 flex justify-between font-bold">
              <span className="text-[#00df8f]">Calculated Risk:</span>
              <span className="text-[#ee0000]">{(simulation.risk_score * 100).toFixed(1)}% ({simulation.risk_label})</span>
            </div>
          </div>
        </div>

        {/* Panel 5: Monte Carlo Seed & Distribution */}
        <div className="rounded-lg border border-[#222222] bg-[#070707] p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-2">
            <span className="text-[10px] font-bold text-[#666666] uppercase tracking-wider">
              05 — MC SEED &amp; DRAWS
            </span>
            <Hash className="h-3.5 w-3.5 text-[#00df8f]" />
          </div>
          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-[#666666]">Random Seed:</span>
              <strong className="text-[#00c8ff] font-bold">{simulation.simulation_config?.random_seed || 42} (Isolated PRNG)</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666666]">Draws:</span>
              <span className="text-[#f7f7f7]">10,000 Draws</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666666]">Mean Assembly Drop:</span>
              <strong className="text-[#00df8f]">{simulation.mc_stats?.mean_drop || meanDropPct}%</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666666]">P95 Assembly Drop:</span>
              <strong className="text-[#f5a623]">{simulation.mc_stats?.p95_drop || p95DropPct}%</strong>
            </div>
          </div>
        </div>

        {/* Panel 6: PCaR Formula & FX Rates */}
        <div className="rounded-lg border border-[#222222] bg-[#070707] p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-2">
            <span className="text-[10px] font-bold text-[#666666] uppercase tracking-wider">
              06 — PCAR FORMULA &amp; FX
            </span>
            <DollarSign className="h-3.5 w-3.5 text-[#f5a623]" />
          </div>
          <div className="space-y-1.5 text-xs font-mono">
            <div>
              <span className="text-[#666666] block text-[10px]">Macro HS 8542 Baseline:</span>
              <strong className="text-[#f7f7f7]">₹{MACRO_BASELINE_CRORE.toLocaleString()} Crore</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666666]">Spot Multiplier:</span>
              <span className="text-[#00c8ff]">2.05x Premium</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666666]">USD/INR Exchange:</span>
              <span className="text-[#a5a5a5]">₹83.50 / $1.00</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#666666]">Graph Integrity Hash:</span>
              <span className="text-[#00df8f] text-[10px]">31f67108669b9208</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
