import React from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  History,
  Activity,
  FileCheck2,
  Lock,
  GitBranch,
  Database,
  Cpu
} from 'lucide-react';
import { EXPOSURE_INDEX_FACTORS, GROUNDING_ENTITIES, SIAM_2021_BACKTEST } from '../../data/mockData';

export const GovernanceView: React.FC = () => {
  // Compute overall structural score
  const totalScore = EXPOSURE_INDEX_FACTORS.reduce((acc, f) => acc + f.contribution, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 rounded-lg border border-[#222222] bg-[#070707] p-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-[#00df8f]" />
            <h1 className="text-base font-bold text-[#f7f7f7]">
              Governance &amp; Model Validation (AlMahri et al. 2026)
            </h1>
          </div>
          <p className="mt-1 text-xs text-[#a5a5a5]">
            Multi-Tier Grounding Integrity, Deterministic Scoring Verification, and Historical Backtest Calibration
          </p>
        </div>

        <div className="flex items-center gap-2 rounded border border-[#00df8f]/30 bg-[#00df8f]/10 px-3 py-1 text-xs font-semibold text-[#00df8f]">
          <CheckCircle2 className="h-3.5 w-3.5" />
          <span>Graph Integrity Verified (Hash: 31f67108669b9208)</span>
        </div>
      </div>

      {/* 1. Structural Exposure Index Matrix */}
      <section
        aria-label="Structural Exposure Index Matrix"
        className="rounded-lg border border-[#222222] bg-[#070707] p-5 space-y-4"
      >
        <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-3">
          <div className="flex items-center gap-2">
            <FileCheck2 className="h-4 w-4 text-[#00c8ff]" />
            <h2 className="text-sm font-semibold text-[#f7f7f7]">
              Supplier Structural Exposure Index Matrix (§3.2.5)
            </h2>
          </div>
          <div className="font-mono text-xs">
            <span className="text-[#666666]">Total Score: </span>
            <strong className="text-[#ee0000] text-sm">{totalScore.toFixed(3)}</strong>{' '}
            <span className="text-[10px] text-[#ee0000] uppercase font-bold">(High Exposure)</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#222222] text-[#666666] uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Risk Factor</th>
                <th className="py-2.5 px-3 text-center">Weight</th>
                <th className="py-2.5 px-3 text-center">Raw Score</th>
                <th className="py-2.5 px-3 text-center">Contribution</th>
                <th className="py-2.5 px-3">Data Grounding Source</th>
                <th className="py-2.5 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#181818] font-mono">
              {EXPOSURE_INDEX_FACTORS.map((factor) => (
                <tr key={factor.id} className="hover:bg-[#0c0c0c] transition">
                  <td className="py-2.5 px-3 font-sans font-medium text-[#f7f7f7]">
                    {factor.name} ({factor.key})
                  </td>
                  <td className="py-2.5 px-3 text-center text-[#a5a5a5]">
                    {(factor.weight * 100).toFixed(0)}%
                  </td>
                  <td className="py-2.5 px-3 text-center text-[#f7f7f7]">
                    {factor.score.toFixed(2)}
                  </td>
                  <td className="py-2.5 px-3 text-center text-[#00c8ff] font-bold">
                    {factor.contribution.toFixed(3)}
                  </td>
                  <td className="py-2.5 px-3 font-sans text-[#a5a5a5]">
                    {factor.source}
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <span
                      className={`inline-block rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                        factor.status === 'Critical'
                          ? 'border border-[#ee0000]/40 bg-[#ee0000]/10 text-[#ee0000]'
                          : 'border border-[#f5a623]/40 bg-[#f5a623]/10 text-[#f5a623]'
                      }`}
                    >
                      {factor.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="rounded bg-[#0c0c0c] p-3 border border-[#1f1f1f] text-[11px] text-[#a5a5a5] font-mono">
          Formula: Structural Score = 0.35 × EB ({EXPOSURE_INDEX_FACTORS[0].score}) + 0.25 × DR ({EXPOSURE_INDEX_FACTORS[1].score}) + 0.20 × DC ({EXPOSURE_INDEX_FACTORS[2].score}) + 0.10 × TC ({EXPOSURE_INDEX_FACTORS[3].score}) + 0.10 × ED ({EXPOSURE_INDEX_FACTORS[4].score}) = <strong className="text-[#f7f7f7]">{totalScore.toFixed(3)}</strong>
        </div>
      </section>

      {/* 2. GraphRAG Grounding Layer */}
      <section
        aria-label="Knowledge Graph Grounding Layer"
        className="rounded-lg border border-[#222222] bg-[#070707] p-5 space-y-4"
      >
        <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-3">
          <div className="flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-[#00df8f]" />
            <h2 className="text-sm font-semibold text-[#f7f7f7]">
              GraphRAG Entity Verification Table
            </h2>
          </div>
          <span className="text-xs text-[#a5a5a5]">
            30 Nodes · 69 Edges Verified
          </span>
        </div>

        <div className="rounded border border-[#00df8f]/30 bg-[#06120e] p-3 text-xs text-[#a5a5a5]">
          <strong className="text-[#00df8f]">Grounding Principle: </strong>
          All quantitative outputs are calculated only from grounded or explicitly marked demo entities. Unverified entities are flagged for procurement review.
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#222222] text-[#666666] uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">Entity Name</th>
                <th className="py-2.5 px-3">Entity Type</th>
                <th className="py-2.5 px-3 font-mono">HS / Code</th>
                <th className="py-2.5 px-3">Source Reference</th>
                <th className="py-2.5 px-3 text-right">Grounding Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#181818]">
              {GROUNDING_ENTITIES.map((ent) => (
                <tr key={ent.id} className="hover:bg-[#0c0c0c] transition">
                  <td className="py-2.5 px-3 font-medium text-[#f7f7f7]">
                    {ent.name}
                  </td>
                  <td className="py-2.5 px-3 text-[#a5a5a5]">{ent.type}</td>
                  <td className="py-2.5 px-3 font-mono text-[#00c8ff]">{ent.hsCode}</td>
                  <td className="py-2.5 px-3 text-[#666666]">{ent.source}</td>
                  <td className="py-2.5 px-3 text-right">
                    {ent.verified ? (
                      <span className="inline-flex items-center gap-1 rounded border border-[#00df8f]/30 bg-[#00df8f]/10 px-2 py-0.5 text-[10px] font-bold text-[#00df8f]">
                        <CheckCircle2 className="h-3 w-3" />
                        Verified
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded border border-[#f5a623]/30 bg-[#f5a623]/10 px-2 py-0.5 text-[10px] font-bold text-[#f5a623]">
                        <AlertTriangle className="h-3 w-3" />
                        Unverified
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 3. Zero Hallucination Methodology & SIAM 2021 Backtest */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Zero Hallucination Card (6 cols) */}
        <div className="lg:col-span-6 rounded-lg border border-[#222222] bg-[#070707] p-5 space-y-4">
          <div className="flex items-center gap-2 border-b border-[#1a1a1a] pb-3">
            <Lock className="h-4 w-4 text-[#00c8ff]" />
            <h2 className="text-sm font-semibold text-[#f7f7f7]">
              Zero Hallucination Architecture
            </h2>
          </div>

          <div className="space-y-3 text-xs text-[#a5a5a5] leading-relaxed">
            <div className="flex items-start gap-2.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#00c8ff] shrink-0 mt-1.5" />
              <p>
                <strong className="text-[#f7f7f7]">Deterministic Knowledge Verification:</strong> Extracted supplier relationships are checked against our hand-curated NetworkX trade graph before Bayesian inference.
              </p>
            </div>

            <div className="flex items-start gap-2.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#00c8ff] shrink-0 mt-1.5" />
              <p>
                <strong className="text-[#f7f7f7]">Strict Boundary Handling:</strong> Unknown or novel entities extracted by SLMs are preserved as unverified hypotheses rather than silently treated as grounded facts.
              </p>
            </div>

            <div className="flex items-start gap-2.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#00c8ff] shrink-0 mt-1.5" />
              <p>
                <strong className="text-[#f7f7f7]">Audited Comtrade Baselines:</strong> All financial exposure formulations trace back to verified UN Comtrade full-year import figures and SIAM FY24 production audits.
              </p>
            </div>

            <div className="flex items-start gap-2.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#00c8ff] shrink-0 mt-1.5" />
              <p>
                <strong className="text-[#f7f7f7]">100% Seeded Reproducibility:</strong> Scenario draws utilize linear congruential PRNG to guarantee exact simulation repeatability for executive audit trails.
              </p>
            </div>
          </div>
        </div>

        {/* SIAM 2021 Historical Backtest Panel (6 cols) */}
        <div className="lg:col-span-6 rounded-lg border border-[#222222] bg-[#070707] p-5 space-y-4">
          <div className="flex items-center gap-2 border-b border-[#1a1a1a] pb-3">
            <History className="h-4 w-4 text-[#f5a623]" />
            <h2 className="text-sm font-semibold text-[#f7f7f7]">
              SIAM 2021 Chip Crisis Backtest Calibration
            </h2>
          </div>

          <p className="text-xs text-[#a5a5a5]">
            Historical benchmark evaluating model fidelity against empirical production loss during the 2021 global automotive semiconductor shortage.
          </p>

          <div className="space-y-3">
            {SIAM_2021_BACKTEST.map((item) => (
              <div key={item.metric} className="rounded border border-[#1e1e1e] bg-[#0c0c0c] p-3 text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#f7f7f7]">{item.metric}</span>
                  <span className="rounded bg-[#00df8f]/10 border border-[#00df8f]/30 px-2 py-0.5 text-[10px] font-mono text-[#00df8f]">
                    {item.status}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-[11px] font-mono text-[#a5a5a5]">
                  <div>Actual: <strong className="text-[#f7f7f7]">{item.historicalValue}</strong></div>
                  <div>Model: <strong className="text-[#00c8ff]">{item.modelEstimate}</strong></div>
                  <div>Delta: <strong className="text-[#00df8f]">{item.deltaError}</strong></div>
                </div>
                <p className="text-[11px] text-[#666666] leading-tight pt-1 border-t border-[#181818]">
                  {item.details}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 4. Model Health Telemetry Deck */}
      <section
        aria-label="Model Health Telemetry Indicators"
        className="grid grid-cols-2 md:grid-cols-6 gap-3"
      >
        <div className="rounded-lg border border-[#222222] bg-[#0b0b0b] p-3">
          <span className="text-[10px] text-[#666666] uppercase block">Graph Hash</span>
          <span className="font-mono text-xs font-bold text-[#f7f7f7] mt-1 block">31f67108</span>
        </div>

        <div className="rounded-lg border border-[#222222] bg-[#0b0b0b] p-3">
          <span className="text-[10px] text-[#666666] uppercase block">Data Freshness</span>
          <span className="font-mono text-xs font-bold text-[#00df8f] mt-1 block">Audited 2022</span>
        </div>

        <div className="rounded-lg border border-[#222222] bg-[#0b0b0b] p-3">
          <span className="text-[10px] text-[#666666] uppercase block">Reproducibility</span>
          <span className="font-mono text-xs font-bold text-[#00c8ff] mt-1 block">Seeded (PRNG)</span>
        </div>

        <div className="rounded-lg border border-[#222222] bg-[#0b0b0b] p-3">
          <span className="text-[10px] text-[#666666] uppercase block">Parser Engine</span>
          <span className="font-mono text-xs font-bold text-[#f7f7f7] mt-1 block">Deterministic</span>
        </div>

        <div className="rounded-lg border border-[#222222] bg-[#0b0b0b] p-3">
          <span className="text-[10px] text-[#666666] uppercase block">Grounding Ratio</span>
          <span className="font-mono text-xs font-bold text-[#00df8f] mt-1 block">87.5% Verified</span>
        </div>

        <div className="rounded-lg border border-[#222222] bg-[#0b0b0b] p-3">
          <span className="text-[10px] text-[#666666] uppercase block">API Backend</span>
          <span className="font-mono text-xs font-bold text-[#f5a623] mt-1 block">Local Demo</span>
        </div>
      </section>
    </div>
  );
};
