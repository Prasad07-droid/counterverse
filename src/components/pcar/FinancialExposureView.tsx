import React, { useState, useMemo } from 'react';
import {
  TrendingDown,
  RefreshCw,
  UploadCloud,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle2,
  DollarSign,
  BarChart3,
  Layers,
  ArrowDownRight,
  Info
} from 'lucide-react';
import { OEMKey, OEMProfile, Currency, ParsedBOM } from '../../types';
import { OEM_PROFILES, CURRENCY_CONFIGS, MACRO_BASELINE_CRORE } from '../../data/mockData';
import { simulateMonteCarlo, formatCurrencyValue, formatPercentage } from '../../utils/formatters';

interface FinancialExposureViewProps {
  selectedOEM: OEMProfile;
  onSelectOEM: (key: OEMKey) => void;
  simulationSeed: number;
}

export const FinancialExposureView: React.FC<FinancialExposureViewProps> = ({
  selectedOEM,
  onSelectOEM,
  simulationSeed,
}) => {
  // Scenario Controls
  const [curtailmentPct, setCurtailmentPct] = useState<number>(35);
  const [recoveryDays, setRecoveryDays] = useState<number>(45);
  const [substitutionPct, setSubstitutionPct] = useState<number>(20);
  const [dependencyPct, setDependencyPct] = useState<number>(selectedOEM.dependencyRatioPct);
  const [sampleSize, setSampleSize] = useState<number>(10000);
  const [activeSeed, setActiveSeed] = useState<number>(simulationSeed);
  const [currency, setCurrency] = useState<Currency>('INR');

  // Custom BOM state
  const [bomFile, setBomFile] = useState<ParsedBOM | null>(null);
  const [bomError, setBomError] = useState<string | null>(null);

  // Compute Monte Carlo dynamically
  const simulationResult = useMemo(() => {
    return simulateMonteCarlo(
      selectedOEM,
      curtailmentPct,
      recoveryDays,
      substitutionPct,
      dependencyPct,
      sampleSize,
      activeSeed
    );
  }, [selectedOEM, curtailmentPct, recoveryDays, substitutionPct, dependencyPct, sampleSize, activeSeed]);

  const handleRecalculate = () => {
    setActiveSeed((prev) => prev + 7);
  };

  // Handle Drag & Drop / File Input
  const handleFileUpload = (file: File) => {
    setBomError(null);
    const validExtensions = ['.csv', '.json'];
    const hasValidExt = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));

    if (!hasValidExt) {
      setBomError('Unsupported file format. Please upload a standard BOM .csv or .json file.');
      return;
    }

    // In-memory demo parsing
    const sizeKb = Number((file.size / 1024).toFixed(1));
    const isJson = file.name.endsWith('.json');
    const mockComponentCount = isJson ? 48 : 64;
    const mockCustomPCaR = Math.round(selectedOEM.allocatedBaselineCr * 0.145 * 2.05);

    setBomFile({
      fileName: file.name,
      fileSizeKb: sizeKb,
      isValid: true,
      componentCount: mockComponentCount,
      criticalComponents: 12,
      calculatedPCaRCrores: mockCustomPCaR,
      parsedAt: new Date().toLocaleTimeString(),
    });
  };

  // Waterfall steps
  const waterfallSteps = useMemo(() => {
    const baseline = MACRO_BASELINE_CRORE;
    const shareAllocated = Math.round(baseline * selectedOEM.marketShare);
    const dependencyScaled = Math.round(shareAllocated * (dependencyPct / 100));
    const meanDropVal = Math.round(dependencyScaled * (simulationResult.meanDropPct / 100));
    const finalPCaR = simulationResult.pcarCrores;

    return [
      { label: 'Audited Macro Baseline', value: baseline, type: 'base' },
      { label: `Market Share (${selectedOEM.marketSharePct}%)`, value: shareAllocated, type: 'scale' },
      { label: `Dependency Ratio (${dependencyPct}%)`, value: dependencyScaled, type: 'scale' },
      { label: `Assembly Drop (${simulationResult.meanDropPct}%)`, value: -meanDropVal, type: 'erosion' },
      { label: 'Final 95% PCaR Exposure', value: finalPCaR, type: 'total' },
    ];
  }, [selectedOEM, dependencyPct, simulationResult]);

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col gap-3 rounded-lg border border-[#222222] bg-[#070707] p-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <TrendingDown className="h-5 w-5 text-[#00c8ff]" />
            <h1 className="text-base font-bold text-[#f7f7f7]">
              Financial Exposure &amp; Procurement Cost-at-Risk (PCaR)
            </h1>
          </div>
          <p className="mt-1 text-xs text-[#a5a5a5]">
            Target OEM:{' '}
            <strong className="text-[#f7f7f7]">{selectedOEM.name}</strong> · Scaled baseline:{' '}
            <span className="font-mono text-[#00c8ff]">
              {formatCurrencyValue(selectedOEM.allocatedBaselineCr, currency)}
            </span>
          </p>
        </div>

        {/* Currency Selector & Recalculate */}
        <div className="flex items-center gap-3">
          <div className="flex items-center rounded border border-[#222222] bg-[#0c0c0c] p-0.5 text-xs font-mono">
            {(['INR', 'USD', 'EUR'] as Currency[]).map((cur) => (
              <button
                key={cur}
                onClick={() => setCurrency(cur)}
                className={`rounded px-2.5 py-1 text-xs font-semibold transition ${
                  currency === cur
                    ? 'bg-[#1787ff] text-white shadow-sm'
                    : 'text-[#666666] hover:text-[#f7f7f7]'
                }`}
              >
                {cur}
              </button>
            ))}
          </div>

          <button
            onClick={handleRecalculate}
            className="flex items-center gap-1.5 rounded-md border border-[#222222] bg-[#ffffff] px-3.5 py-1.5 text-xs font-bold text-black hover:bg-[#eaeaea] transition shadow-md"
          >
            <RefreshCw className="h-3.5 w-3.5 text-black" />
            <span>Recalculate Exposure</span>
          </button>
        </div>
      </div>

      {/* Grid: Scenario Controls (Left) + Monte Carlo Chart (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Controls Column (5 cols) */}
        <div className="lg:col-span-5 rounded-lg border border-[#222222] bg-[#070707] p-5 space-y-5">
          <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-3">
            <h2 className="text-xs font-bold tracking-widest text-[#666666] uppercase">
              SCENARIO STRESS CONTROLS
            </h2>
            <span className="font-mono text-[11px] text-[#00c8ff]">Seed: {activeSeed}</span>
          </div>

          {/* OEM Selection dropdown */}
          <div>
            <label htmlFor="pcar-oem-select" className="text-xs text-[#a5a5a5] font-medium block mb-1.5">
              Select Enterprise OEM Profile
            </label>
            <select
              id="pcar-oem-select"
              value={selectedOEM.id}
              onChange={(e) => {
                const key = e.target.value as OEMKey;
                onSelectOEM(key);
                setDependencyPct(OEM_PROFILES[key].dependencyRatioPct);
              }}
              className="w-full rounded border border-[#222222] bg-[#0b0b0b] px-3 py-2 text-xs text-[#f7f7f7] focus:border-[#00c8ff] focus:outline-none cursor-pointer"
            >
              {Object.values(OEM_PROFILES).map((prof) => (
                <option key={prof.id} value={prof.id}>
                  {prof.name} ({prof.marketSharePct}% Share · {prof.dependencyRatioPct}% Dependency)
                </option>
              ))}
            </select>
          </div>

          {/* Sliders */}
          <div className="space-y-4 text-xs">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-[#a5a5a5]">Assembly Curtailment:</span>
                <span className="font-mono font-bold text-[#f7f7f7]">{curtailmentPct}%</span>
              </div>
              <input
                type="range"
                min="5"
                max="85"
                value={curtailmentPct}
                onChange={(e) => setCurtailmentPct(Number(e.target.value))}
                className="w-full accent-[#00c8ff] cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-[#a5a5a5]">Recovery Duration:</span>
                <span className="font-mono font-bold text-[#f7f7f7]">{recoveryDays} Days</span>
              </div>
              <input
                type="range"
                min="10"
                max="120"
                value={recoveryDays}
                onChange={(e) => setRecoveryDays(Number(e.target.value))}
                className="w-full accent-[#00c8ff] cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-[#a5a5a5]">Supplier Substitution Capacity:</span>
                <span className="font-mono font-bold text-[#00df8f]">{substitutionPct}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="60"
                value={substitutionPct}
                onChange={(e) => setSubstitutionPct(Number(e.target.value))}
                className="w-full accent-[#00df8f] cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-[#a5a5a5]">Import Dependency:</span>
                <span className="font-mono font-bold text-[#f5a623]">{dependencyPct}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="100"
                value={dependencyPct}
                onChange={(e) => setDependencyPct(Number(e.target.value))}
                className="w-full accent-[#f5a623] cursor-pointer"
              />
            </div>
          </div>

          {/* Sample Size Toggle */}
          <div className="border-t border-[#1a1a1a] pt-4">
            <span className="text-[10px] font-bold tracking-widest text-[#666666] uppercase block mb-2">
              SIMULATION SAMPLE SIZE
            </span>
            <div className="grid grid-cols-5 gap-1 text-[11px] font-mono">
              {[500, 1000, 10000, 25000, 50000].map((sz) => (
                <button
                  key={sz}
                  onClick={() => setSampleSize(sz)}
                  className={`rounded border py-1.5 transition ${
                    sampleSize === sz
                      ? 'border-[#00c8ff] bg-[#00c8ff]/15 text-[#00c8ff] font-bold'
                      : 'border-[#222222] bg-[#0b0b0b] text-[#666666] hover:text-[#f7f7f7]'
                  }`}
                >
                  {sz >= 1000 ? `${sz / 1000}k` : sz}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Monte Carlo Histogram (7 cols) */}
        <div className="lg:col-span-7 rounded-lg border border-[#222222] bg-[#070707] p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-[#00df8f]" />
              <h2 className="text-sm font-semibold text-[#f7f7f7]">
                Monte Carlo Output Drop Distribution
              </h2>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="text-[#00df8f]">Mean: {simulationResult.meanDropPct}%</span>
              <span className="text-[#f5a623]">P95: {simulationResult.p95DropPct}%</span>
              <span className="text-[#ee0000]">P99: {simulationResult.p99DropPct}%</span>
            </div>
          </div>

          {/* SVG Histogram */}
          <div className="my-4 h-64 w-full">
            <svg viewBox="0 0 600 220" className="w-full h-full" role="img" aria-label="Monte Carlo Distribution Histogram">
              {/* Axes lines */}
              <line x1="40" y1="180" x2="580" y2="180" stroke="#222222" strokeWidth="1" />
              <line x1="40" y1="20" x2="40" y2="180" stroke="#222222" strokeWidth="1" />

              {/* Bars */}
              {simulationResult.distributionBars.map((bar, idx) => {
                const maxPercent = 25;
                const barHeight = Math.min(150, (bar.percentage / maxPercent) * 150);
                const x = 50 + idx * 32;
                const y = 180 - barHeight;

                const isP95 = bar.isP95;
                const isP99 = bar.isP99;

                return (
                  <g key={`bar-${idx}`} className="group cursor-pointer">
                    <rect
                      x={x}
                      y={y}
                      width="26"
                      height={barHeight}
                      rx="3"
                      fill={isP99 ? '#ee0000' : isP95 ? '#f5a623' : '#1787ff'}
                      fillOpacity={isP99 || isP95 ? 0.9 : 0.65}
                      className="transition-all hover:fill-opacity-100"
                    />

                    {/* Tooltip on hover */}
                    <text
                      x={x + 13}
                      y={y - 6}
                      textAnchor="middle"
                      fill="#ffffff"
                      fontSize="9"
                      fontFamily="Geist Mono"
                      className="opacity-0 group-hover:opacity-100 transition-opacity font-bold"
                    >
                      {bar.percentage.toFixed(1)}%
                    </text>

                    {/* X-axis label */}
                    <text
                      x={x + 13}
                      y="196"
                      textAnchor="middle"
                      fill="#666666"
                      fontSize="8"
                      fontFamily="Geist Mono"
                    >
                      {bar.binLabel.split('-')[0]}%
                    </text>
                  </g>
                );
              })}

              {/* Vertical Markers */}
              <text x="310" y="215" textAnchor="middle" fill="#a5a5a5" fontSize="10">
                Assembly Production Drop (%)
              </text>
            </svg>
          </div>

          {/* Metric Summary Footnote */}
          <div className="grid grid-cols-2 gap-3 border-t border-[#1a1a1a] pt-3 text-xs">
            <div className="rounded bg-[#0c0c0c] p-2.5 border border-[#1f1f1f]">
              <span className="text-[#666666] block text-[11px]">95% Procurement Cost-at-Risk:</span>
              <span className="font-mono text-base font-bold text-[#00c8ff]">
                {formatCurrencyValue(simulationResult.pcarCrores, currency)}
              </span>
            </div>
            <div className="rounded bg-[#0c0c0c] p-2.5 border border-[#1f1f1f]">
              <span className="text-[#666666] block text-[11px]">Expected Baseline Loss:</span>
              <span className="font-mono text-base font-bold text-[#f7f7f7]">
                {formatCurrencyValue(simulationResult.meanLossCrores, currency)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* PCaR Waterfall Section */}
      <section
        aria-label="PCaR Waterfall Decomposition"
        className="rounded-lg border border-[#222222] bg-[#070707] p-5 space-y-4"
      >
        <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-3">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-[#1787ff]" />
            <h2 className="text-sm font-semibold text-[#f7f7f7]">
              Financial Exposure Waterfall (PCaR Formulation)
            </h2>
          </div>
          <span className="text-xs text-[#a5a5a5] font-mono">
            Demo Currency Conversion: INR 1.0 = USD 0.012 = EUR 0.011
          </span>
        </div>

        {/* Waterfall Card Deck */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {waterfallSteps.map((step, idx) => (
            <div
              key={step.label}
              className={`rounded-md border p-3 flex flex-col justify-between ${
                step.type === 'total'
                  ? 'border-[#00c8ff]/40 bg-[#00c8ff]/10'
                  : step.type === 'erosion'
                  ? 'border-[#ee0000]/30 bg-[#0c0606]'
                  : 'border-[#222222] bg-[#0b0b0b]'
              }`}
            >
              <div className="flex items-center justify-between text-[11px] font-semibold text-[#666666]">
                <span>STEP 0{idx + 1}</span>
                {step.type === 'erosion' ? (
                  <ArrowDownRight className="h-3 w-3 text-[#ee0000]" />
                ) : null}
              </div>
              <div className="my-2">
                <span className="text-xs text-[#a5a5a5] block leading-tight">{step.label}</span>
                <span
                  className={`font-mono text-base font-bold mt-1 block ${
                    step.type === 'total'
                      ? 'text-[#00c8ff]'
                      : step.type === 'erosion'
                      ? 'text-[#ee0000]'
                      : 'text-[#f7f7f7]'
                  }`}
                >
                  {formatCurrencyValue(Math.abs(step.value), currency)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Custom BOM Uploader */}
      <section
        aria-label="Custom Bill of Materials Analysis"
        className="rounded-lg border border-[#222222] bg-[#070707] p-5 space-y-4"
      >
        <div className="flex items-center gap-2 border-b border-[#1a1a1a] pb-3">
          <FileSpreadsheet className="h-4 w-4 text-[#00df8f]" />
          <h2 className="text-sm font-semibold text-[#f7f7f7]">
            Custom Bill of Materials (BOM) Enterprise Ingest
          </h2>
        </div>

        {/* Drag & Drop Zone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
              handleFileUpload(e.dataTransfer.files[0]);
            }
          }}
          className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-[#222222] bg-[#0b0b0b] p-8 text-center hover:border-[#3a3a3a] transition cursor-pointer"
          onClick={() => {
            document.getElementById('bom-file-input')?.click();
          }}
        >
          <UploadCloud className="h-8 w-8 text-[#666666] mb-2" />
          <p className="text-xs font-medium text-[#f7f7f7]">
            Drag and drop custom enterprise BOM <span className="font-mono text-[#00c8ff]">.CSV</span> or{' '}
            <span className="font-mono text-[#00c8ff]">.JSON</span>
          </p>
          <p className="text-[11px] text-[#666666] mt-1">
            Local browser parsing only · Zero external data transmission
          </p>

          <input
            id="bom-file-input"
            type="file"
            accept=".csv,.json"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileUpload(e.target.files[0]);
              }
            }}
          />
        </div>

        {/* BOM Validation Error */}
        {bomError && (
          <div className="flex items-center gap-2 rounded border border-[#ee0000]/30 bg-[#ee0000]/10 p-3 text-xs text-[#ee0000]">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{bomError}</span>
          </div>
        )}

        {/* Parsed BOM Result Card */}
        {bomFile && (
          <div className="rounded-lg border border-[#00df8f]/30 bg-[#06120e] p-4 text-xs space-y-2">
            <div className="flex items-center justify-between border-b border-[#00df8f]/20 pb-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00df8f]" />
                <span className="font-semibold text-[#f7f7f7]">{bomFile.fileName}</span>
                <span className="rounded bg-[#00df8f]/20 px-2 py-0.5 text-[10px] text-[#00df8f]">
                  Valid Schema
                </span>
              </div>
              <span className="text-[#666666]">{bomFile.fileSizeKb} KB</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2 text-[#a5a5a5]">
              <div>
                <span>Components Parsed:</span>
                <strong className="block text-sm text-[#f7f7f7] font-mono mt-0.5">
                  {bomFile.componentCount}
                </strong>
              </div>
              <div>
                <span>Single-Source Critical:</span>
                <strong className="block text-sm text-[#f5a623] font-mono mt-0.5">
                  {bomFile.criticalComponents}
                </strong>
              </div>
              <div>
                <span>Calculated Custom PCaR:</span>
                <strong className="block text-sm text-[#00c8ff] font-mono mt-0.5">
                  {formatCurrencyValue(bomFile.calculatedPCaRCrores, currency)}
                </strong>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
};
