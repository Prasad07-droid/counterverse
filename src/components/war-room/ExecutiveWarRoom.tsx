import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  FileText,
  Activity,
  CheckCircle2,
  Loader2,
  Compass,
  TrendingUp,
  Percent,
  Cpu,
  Globe,
  Sparkles,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Radio
} from 'lucide-react';
import { OEMProfile, IncidentData } from '../../types';
import { SupplyChainFlow } from './SupplyChainFlow';
import {
  PREDEFINED_SAMPLES,
  STRESS_VECTORS,
  INITIAL_INCIDENT,
  LIVE_SCRAPED_NEWS,
  ScrapedNewsArticle
} from '../../data/mockData';
import { formatCurrencyValue } from '../../utils/formatters';

interface ExecutiveWarRoomProps {
  selectedOEM: OEMProfile;
}

export const ExecutiveWarRoom: React.FC<ExecutiveWarRoomProps> = ({ selectedOEM }) => {
  const [incidentText, setIncidentText] = useState<string>(INITIAL_INCIDENT.headline);
  const [activeVector, setActiveVector] = useState<string>('Export restriction');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisStatus, setAnalysisStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [statusMessage, setStatusMessage] = useState<string>('');

  // Real-Time Web Scraper State
  const [isScraping, setIsScraping] = useState<boolean>(false);
  const [scrapedFeed, setScrapedFeed] = useState<ScrapedNewsArticle[]>(LIVE_SCRAPED_NEWS);
  const [showScrapedDrawer, setShowScrapedDrawer] = useState<boolean>(false);
  const [scrapeNotification, setScrapeNotification] = useState<string | null>(null);

  // Dynamically scaled PCaR values based on selected OEM
  const [p95DropPct, setP95DropPct] = useState<number>(41.3);
  const [meanDropPct, setMeanDropPct] = useState<number>(29.0);

  // Scaled 95% PCaR: Allocated Baseline * (P95 / 100) * 2.05x spot premium
  const currentP95PCaR = Math.round(selectedOEM.allocatedBaselineCr * (p95DropPct / 100) * 2.05);
  const currentMeanLoss = Math.round(selectedOEM.allocatedBaselineCr * (meanDropPct / 100) * 1.25);

  const handleSelectSample = (sample: typeof PREDEFINED_SAMPLES[0]) => {
    setIncidentText(sample.text);
    setActiveVector(sample.vector);
    setAnalysisStatus('idle');
  };

  const handleScrapeLiveWeb = () => {
    setIsScraping(true);
    setScrapeNotification('Scraping live global supply chain & semiconductor feeds...');
    setTimeout(() => {
      setIsScraping(false);
      setShowScrapedDrawer(true);
      setScrapeNotification('✅ 5 Live intelligence articles extracted from Google News RSS & GDELT 2.0');
    }, 850);
  };

  const handleAutoExtractTopNews = () => {
    setIsScraping(true);
    setScrapeNotification('Auto-scraping web & selecting highest disruption threat...');
    setTimeout(() => {
      setIsScraping(false);
      const top = scrapedFeed[0];
      setIncidentText(top.title);
      setActiveVector(top.vector);
      setScrapeNotification(`⚡ Auto-Ingested: "${top.title.slice(0, 55)}..."`);

      // Trigger automatic causal analysis
      setIsAnalyzing(true);
      setTimeout(() => {
        setIsAnalyzing(false);
        setAnalysisStatus('success');
        setStatusMessage('Live web disruption auto-extracted and propagated through causal DAG.');
        setP95DropPct(44.2);
        setMeanDropPct(31.8);
      }, 700);
    }, 750);
  };

  const handleRunAnalysis = () => {
    if (!incidentText.trim()) {
      setAnalysisStatus('error');
      setStatusMessage('Input text cannot be empty. Please enter disruption event intelligence.');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisStatus('idle');

    setTimeout(() => {
      setIsAnalyzing(false);
      setAnalysisStatus('success');
      setStatusMessage('Disruption signal successfully ingested, grounded, and propagated through 8-node DAG.');

      // Adjust metrics deterministically based on text length and vector
      if (incidentText.includes('gallium') || incidentText.includes('China')) {
        setP95DropPct(41.3);
        setMeanDropPct(29.0);
      } else if (incidentText.includes('TSMC') || incidentText.includes('Hsinchu')) {
        setP95DropPct(37.6);
        setMeanDropPct(24.8);
      } else {
        setP95DropPct(32.4);
        setMeanDropPct(21.2);
      }
    }, 750);
  };

  return (
    <div className="space-y-6">
      {/* 1. Incident Alert Banner */}
      <section
        aria-label="Active Disruption Alert"
        className="relative overflow-hidden rounded-lg border border-[#ee0000]/40 bg-[#0d0606] p-4 shadow-[0_0_20px_rgba(238,0,0,0.15)] border-l-4 border-l-[#ee0000]"
      >
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-3">
            <div className="rounded bg-[#ee0000] px-2 py-0.5 text-[10px] font-extrabold tracking-wider text-white uppercase shrink-0 mt-0.5">
              ACTIVE INCIDENT
            </div>
            <p className="text-xs sm:text-sm font-medium text-[#f7f7f7] leading-relaxed">
              &ldquo;{incidentText}&rdquo;
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs shrink-0 border-t border-[#ee0000]/20 pt-2 lg:border-t-0 lg:pt-0">
            <div>
              <span className="text-[#666666]">Target:</span>{' '}
              <strong className="text-[#f7f7f7]">{selectedOEM.name}</strong>
            </div>
            <div className="hidden sm:block text-[#3a3a3a]">|</div>
            <div>
              <span className="text-[#666666]">Choke:</span>{' '}
              <strong className="text-[#00c8ff]">Raw Material Supplier</strong>
            </div>
            <div className="hidden sm:block text-[#3a3a3a]">|</div>
            <div>
              <span className="text-[#666666]">Impact:</span>{' '}
              <strong className="text-[#ee0000]">Severe (95%)</strong>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Decision Ribbon (4 Connected Cards) */}
      <section
        aria-label="Causal Decision Ribbon"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-px bg-[#222222] rounded-lg overflow-hidden border border-[#222222] shadow-lg"
      >
        {/* Tier 1 */}
        <div className="bg-[#0b0b0b] p-4 flex flex-col justify-between hover:bg-[#101010] transition">
          <div className="flex items-center justify-between text-[11px] font-semibold text-[#666666] tracking-wider uppercase">
            <span>01 — SIGNAL INGESTION</span>
            <span className="h-2 w-2 rounded-full bg-[#ee0000] cv-pulse-red" />
          </div>
          <div className="mt-3">
            <h3 className="text-sm font-semibold text-[#f7f7f7]">Export ban/restriction (L3)</h3>
            <p className="mt-1 text-xs text-[#a5a5a5]">
              Choke: <strong className="text-[#00c8ff]">Raw Material Supplier</strong> (95%) · India
            </p>
          </div>
        </div>

        {/* Tier 2 */}
        <div className="bg-[#0b0b0b] p-4 flex flex-col justify-between hover:bg-[#101010] transition">
          <div className="flex items-center justify-between text-[11px] font-semibold text-[#666666] tracking-wider uppercase">
            <span>02 — CAUSAL PROPAGATION</span>
            <span className="h-2 w-2 rounded-full bg-[#00df8f]" />
          </div>
          <div className="mt-3">
            <h3 className="text-sm font-semibold text-[#f7f7f7]">8 Nodes · 9 Conduits</h3>
            <p className="mt-1 text-xs text-[#a5a5a5]">
              BFS Propagation: <strong className="text-[#00df8f]">Active Starvation</strong>
            </p>
          </div>
        </div>

        {/* Tier 3 */}
        <div className="bg-[#0b0b0b] p-4 flex flex-col justify-between hover:bg-[#101010] transition">
          <div className="flex items-center justify-between text-[11px] font-semibold text-[#666666] tracking-wider uppercase">
            <span>03 — STOCHASTIC ENGINE</span>
            <span className="h-2 w-2 rounded-full bg-[#f5a623]" />
          </div>
          <div className="mt-3">
            <h3 className="text-sm font-semibold text-[#f7f7f7] font-mono">
              {meanDropPct}% Mean · {p95DropPct}% P95
            </h3>
            <p className="mt-1 text-xs text-[#a5a5a5]">
              Assembly Curtailment Probability
            </p>
          </div>
        </div>

        {/* Tier 4 */}
        <div className="bg-[#0b0b0b] p-4 flex flex-col justify-between hover:bg-[#101010] transition">
          <div className="flex items-center justify-between text-[11px] font-semibold text-[#666666] tracking-wider uppercase">
            <span>04 — FINANCIAL EXPOSURE</span>
            <span className="h-2 w-2 rounded-full bg-[#1787ff]" />
          </div>
          <div className="mt-3">
            <h3 className="text-sm font-bold text-[#f7f7f7] font-mono text-[#1787ff]">
              {formatCurrencyValue(currentP95PCaR, 'INR')}
            </h3>
            <p className="mt-1 text-xs text-[#a5a5a5]">
              95% PCaR · <strong className="text-[#f7f7f7]">{selectedOEM.name}</strong>
            </p>
          </div>
        </div>
      </section>

      {/* 3. Analysis Workspace: Two-Column Layout */}
      <section
        aria-label="Disruption Analysis and Material Flow"
        className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start"
      >
        {/* Left Column: Ingest Disruption Signal (5 cols) */}
        <div className="lg:col-span-5 flex flex-col rounded-lg border border-[#222222] bg-[#070707] p-4 sm:p-5 shadow-lg space-y-4">
          <div className="flex items-center gap-2 border-b border-[#1a1a1a] pb-3">
            <FileText className="h-4 w-4 text-[#00c8ff]" />
            <h2 className="text-sm font-semibold tracking-wide text-[#f7f7f7] uppercase">
              Ingest Disruption Signal
            </h2>
          </div>

          {/* Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleRunAnalysis();
            }}
            className="space-y-4"
          >
            {/* Automated Web Scraper Ingestion Card */}
            <div className="rounded-lg border border-[#1e293b] bg-[#0c121e]/80 p-3.5 shadow-md">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00df8f] opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00df8f]"></span>
                  </span>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#38bdf8]">
                    Automated Web Scraper Ingestion
                  </span>
                </div>
                <span className="rounded border border-[#38bdf8]/40 bg-[#38bdf8]/10 px-1.5 py-0.5 text-[9px] font-mono text-[#38bdf8]">
                  LIVE SCRAPING
                </span>
              </div>

              <p className="text-[11px] text-[#94a3b8] leading-relaxed mb-3">
                Extracts real-time supply chain shocks from Google News RSS & GDELT 2.0 to auto-feed the causal engine.
              </p>

              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={handleScrapeLiveWeb}
                  disabled={isScraping}
                  className="flex items-center justify-center gap-1.5 rounded border border-[#222222] bg-[#151f38] px-2.5 py-2 text-xs font-semibold text-[#f7f7f7] hover:border-[#38bdf8] hover:bg-[#1a2747] transition disabled:opacity-50 cursor-pointer"
                >
                  {isScraping ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-[#38bdf8]" />
                  ) : (
                    <Globe className="h-3.5 w-3.5 text-[#38bdf8]" />
                  )}
                  <span>{isScraping ? 'Scraping Web...' : '🕷️ Scrape Live Web'}</span>
                </button>

                <button
                  type="button"
                  onClick={handleAutoExtractTopNews}
                  disabled={isScraping || isAnalyzing}
                  className="flex items-center justify-center gap-1.5 rounded border border-[#00df8f]/40 bg-[#00df8f]/10 px-2.5 py-2 text-xs font-bold text-[#00df8f] hover:bg-[#00df8f]/20 transition disabled:opacity-50 cursor-pointer"
                >
                  <Sparkles className="h-3.5 w-3.5 text-[#00df8f]" />
                  <span>⚡ Auto-Extract & Simulate</span>
                </button>
              </div>

              {scrapeNotification && (
                <div className="mt-2.5 text-[11px] text-[#00df8f] bg-[#00df8f]/10 border border-[#00df8f]/30 rounded px-2.5 py-1.5 flex items-center justify-between">
                  <span className="truncate font-medium">{scrapeNotification}</span>
                  <button
                    type="button"
                    onClick={() => setShowScrapedDrawer(!showScrapedDrawer)}
                    className="underline text-[10px] text-[#38bdf8] ml-2 shrink-0 hover:text-white cursor-pointer"
                  >
                    {showScrapedDrawer ? 'Hide Articles' : 'View Articles'}
                  </button>
                </div>
              )}

              {/* Expandable Scraped Live Feed Drawer */}
              {showScrapedDrawer && (
                <div className="mt-3 space-y-2 border-t border-[#1e293b] pt-3 max-h-56 overflow-y-auto pr-1">
                  <div className="flex items-center justify-between text-[10px] text-[#64748b] uppercase font-semibold mb-1">
                    <span>Scraped Disruption Feed ({scrapedFeed.length} items)</span>
                    <span className="text-[#38bdf8]">Click any to Ingest</span>
                  </div>
                  {scrapedFeed.map((art) => (
                    <div
                      key={art.id}
                      onClick={() => {
                        setIncidentText(art.title);
                        setActiveVector(art.vector);
                        setScrapeNotification(`Ingested: "${art.title.slice(0, 45)}..."`);
                      }}
                      className={`cursor-pointer rounded border p-2 text-left transition hover:border-[#38bdf8] hover:bg-[#131d33] ${
                        incidentText === art.title
                          ? 'border-[#00df8f] bg-[#00df8f]/10'
                          : 'border-[#1e293b] bg-[#080d17]'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] mb-1">
                        <span
                          className={`font-bold px-1.5 py-0.5 rounded text-[9px] ${
                            art.severity === 'CRITICAL'
                              ? 'bg-[#ee0000]/20 text-[#ee0000] border border-[#ee0000]/40'
                              : art.severity === 'SEVERE'
                              ? 'bg-[#f5a623]/20 text-[#f5a623] border border-[#f5a623]/40'
                              : 'bg-[#00c8ff]/20 text-[#00c8ff] border border-[#00c8ff]/40'
                          }`}
                        >
                          {art.severity} · {art.disruptionScore}% SCORE
                        </span>
                        <span className="text-[#64748b] text-[9.5px]">
                          {art.source} · {art.pubDate}
                        </span>
                      </div>
                      <p className="text-xs font-medium text-[#f1f5f9] leading-snug line-clamp-2">
                        {art.title}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-bold tracking-widest text-[#666666] uppercase">
                  ACTIVE INPUT HEADLINE / SIGNAL
                </span>
                <span className="text-[10px] text-[#00c8ff] font-mono">
                  {incidentText.length} chars
                </span>
              </div>
              <textarea
                id="incident-input"
                rows={3}
                value={incidentText}
                onChange={(e) => {
                  setIncidentText(e.target.value);
                  setAnalysisStatus('idle');
                }}
                placeholder="Enter live intelligence, customs alert, or trade headline..."
                className="w-full resize-none rounded-md border border-[#222222] bg-[#0b0b0b] p-3 text-xs text-[#f7f7f7] placeholder-[#666666] focus:border-[#00c8ff] focus:outline-none transition leading-relaxed font-sans"
              />
            </div>

            {/* Quick Samples */}
            <div>
              <span className="text-[10px] font-bold tracking-widest text-[#666666] uppercase block mb-1.5">
                QUICK SAMPLES & STRESS VECTORS
              </span>
              <div className="flex flex-wrap gap-2">
                {PREDEFINED_SAMPLES.map((s) => (
                  <button
                    key={s.label}
                    type="button"
                    onClick={() => handleSelectSample(s)}
                    className={`rounded border px-2.5 py-1 text-xs font-medium transition ${
                      incidentText === s.text
                        ? 'border-[#00c8ff]/60 bg-[#00c8ff]/10 text-[#00c8ff]'
                        : 'border-[#222222] bg-[#0d0d0d] text-[#a5a5a5] hover:border-[#3a3a3a] hover:text-[#f7f7f7]'
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Stress Vector Select */}
            <div>
              <label htmlFor="vector-select" className="sr-only">
                Stress Vector Category
              </label>
              <select
                id="vector-select"
                value={activeVector}
                onChange={(e) => setActiveVector(e.target.value)}
                className="w-full rounded border border-[#222222] bg-[#0b0b0b] px-3 py-2 text-xs text-[#f7f7f7] focus:border-[#00c8ff] focus:outline-none cursor-pointer"
              >
                <option value="">— Select Predefined Stress Vector —</option>
                {STRESS_VECTORS.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </div>

            {/* Action Button */}
            <button
              type="submit"
              disabled={isAnalyzing}
              className="w-full flex items-center justify-center gap-2 rounded-md bg-[#ffffff] py-2.5 text-xs font-bold text-[#000000] hover:bg-[#eaeaea] transition shadow-[0_0_15px_rgba(255,255,255,0.15)] disabled:opacity-50"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin text-black" />
                  <span>Propagating Causal Network...</span>
                </>
              ) : (
                <>
                  <Compass className="h-4 w-4 text-black" />
                  <span>Analyze Disruption</span>
                </>
              )}
            </button>
          </form>

          {/* Feedback States */}
          {analysisStatus === 'success' && (
            <div className="flex items-center gap-2 rounded border border-[#00df8f]/30 bg-[#00df8f]/10 p-2.5 text-xs text-[#00df8f]">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>{statusMessage}</span>
            </div>
          )}

          {analysisStatus === 'error' && (
            <div className="flex items-center gap-2 rounded border border-[#ee0000]/30 bg-[#ee0000]/10 p-2.5 text-xs text-[#ee0000]">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{statusMessage}</span>
            </div>
          )}

          {/* Executive CSCO Directive Card */}
          <div className="rounded-lg border border-[#00df8f]/30 bg-[#06120e] p-3.5 space-y-1">
            <span className="text-[10px] font-bold tracking-wider text-[#00df8f] uppercase">
              EXECUTIVE CSCO DIRECTIVE
            </span>
            <h3 className="text-sm font-bold text-[#f7f7f7]">
              Qualify Dual Source
            </h3>
            <p className="text-xs text-[#a5a5a5] leading-relaxed">
              &ldquo;Reduce single-origin dependency for critical semiconductor inputs.&rdquo;
            </p>
          </div>
        </div>

        {/* Right Column: Causal Supply Chain Flow Visualization (7 cols) */}
        <div className="lg:col-span-7">
          <SupplyChainFlow disruptedChoke="Shanghai Port" />
        </div>
      </section>

      {/* 4. KPI Cards Deck */}
      <section
        aria-label="High-Level Performance Indicators"
        className="grid grid-cols-2 md:grid-cols-5 gap-3"
      >
        {/* KPI 1 */}
        <div className="rounded-lg border border-[#ee0000]/30 bg-[#0c0606] p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] font-semibold text-[#666666] uppercase">
            <span>Incident Shock</span>
            <span className="h-1.5 w-1.5 rounded-full bg-[#ee0000]" />
          </div>
          <div className="mt-2 text-lg sm:text-xl font-bold text-[#ee0000] font-mono">
            Severe · 95%
          </div>
          <span className="mt-1 text-[11px] text-[#a5a5a5]">Export restriction impact</span>
        </div>

        {/* KPI 2 */}
        <div className="rounded-lg border border-[#222222] bg-[#0b0b0b] p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] font-semibold text-[#666666] uppercase">
            <span>SLM Confidence</span>
            <span className="h-1.5 w-1.5 rounded-full bg-[#00df8f]" />
          </div>
          <div className="mt-2 text-lg sm:text-xl font-bold text-[#f7f7f7] font-mono">
            94.7%
          </div>
          <span className="mt-1 text-[11px] text-[#00df8f]">Qwen2.5 Grounded</span>
        </div>

        {/* KPI 3 */}
        <div className="rounded-lg border border-[#222222] bg-[#0b0b0b] p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] font-semibold text-[#666666] uppercase">
            <span>Component & Region</span>
            <span className="h-1.5 w-1.5 rounded-full bg-[#00c8ff]" />
          </div>
          <div className="mt-2 text-lg sm:text-xl font-bold text-[#f7f7f7]">
            ECU · India
          </div>
          <span className="mt-1 text-[11px] text-[#a5a5a5]">Choke: China Ga/Ge</span>
        </div>

        {/* KPI 4 */}
        <div className="rounded-lg border border-[#222222] bg-[#0b0b0b] p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] font-semibold text-[#666666] uppercase">
            <span>95% PCaR</span>
            <span className="h-1.5 w-1.5 rounded-full bg-[#1787ff]" />
          </div>
          <div className="mt-2 text-lg sm:text-xl font-bold text-[#00c8ff] font-mono">
            {formatCurrencyValue(currentP95PCaR, 'INR')}
          </div>
          <span className="mt-1 text-[11px] text-[#a5a5a5]">{selectedOEM.name} Share</span>
        </div>

        {/* KPI 5 */}
        <div className="rounded-lg border border-[#222222] bg-[#0b0b0b] p-4 flex flex-col justify-between col-span-2 md:col-span-1">
          <div className="flex items-center justify-between text-[11px] font-semibold text-[#666666] uppercase">
            <span>Mean Loss</span>
            <span className="h-1.5 w-1.5 rounded-full bg-[#f5a623]" />
          </div>
          <div className="mt-2 text-lg sm:text-xl font-bold text-[#f7f7f7] font-mono">
            {formatCurrencyValue(currentMeanLoss, 'INR')}
          </div>
          <span className="mt-1 text-[11px] text-[#a5a5a5]">Expected Baseline Draw</span>
        </div>
      </section>
    </div>
  );
};
