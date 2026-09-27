import React from 'react';
import {
  ShieldAlert,
  TrendingDown,
  FileCheck2,
  Cpu,
  Layers,
  Settings,
  ChevronDown,
  X
} from 'lucide-react';
import { NavView, OEMKey, ExtractionEngine } from '../../types';
import { OEM_PROFILES } from '../../data/mockData';

interface SidebarProps {
  currentView: NavView;
  onSelectView: (view: NavView) => void;
  selectedOEMKey: OEMKey;
  onSelectOEM: (key: OEMKey) => void;
  extractionEngine: ExtractionEngine;
  onSelectEngine: (engine: ExtractionEngine) => void;
  onOpenSettings: () => void;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onSelectView,
  selectedOEMKey,
  onSelectOEM,
  extractionEngine,
  onSelectEngine,
  onOpenSettings,
  isOpenMobile,
  onCloseMobile,
}) => {
  const currentOEM = OEM_PROFILES[selectedOEMKey];

  const navItems: { id: NavView; label: string; icon: React.ReactNode }[] = [
    {
      id: 'war-room',
      label: '01 — Executive War Room',
      icon: <ShieldAlert className="h-4 w-4" />,
    },
    {
      id: 'financial-exposure',
      label: '02 — Financial Exposure & PCaR',
      icon: <TrendingDown className="h-4 w-4" />,
    },
    {
      id: 'governance',
      label: '03 — Governance & Model Validation',
      icon: <FileCheck2 className="h-4 w-4" />,
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 z-40 bg-black/80 backdrop-blur-sm lg:hidden"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex w-72 flex-col justify-between border-r border-[#222222] bg-[#050505] transition-transform duration-200 lg:static lg:translate-x-0 ${
          isOpenMobile ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col p-4 sm:p-5 overflow-y-auto no-scrollbar">
          {/* Top Branding */}
          <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-4">
            <div className="flex items-center gap-3">
              {/* White rounded square logo with geometric triangle */}
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#f7f7f7] shadow-[0_0_15px_rgba(255,255,255,0.2)]">
                <svg
                  viewBox="0 0 24 24"
                  className="h-4 w-4 fill-black text-black"
                  aria-hidden="true"
                >
                  <polygon points="12 4 21 20 3 20" />
                </svg>
              </div>
              <div>
                <h1 className="text-base font-bold tracking-tight text-[#f7f7f7]">
                  CounterVerse
                </h1>
                <p className="text-[10px] font-semibold tracking-wider text-[#666666] uppercase">
                  SUPPLY CHAIN INTELLIGENCE
                </p>
              </div>
            </div>

            {/* Mobile close button */}
            <button
              onClick={onCloseMobile}
              className="rounded p-1 text-[#666666] hover:bg-[#151515] hover:text-[#f7f7f7] lg:hidden"
              aria-label="Close sidebar menu"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Locked Scope Badge */}
          <div className="mt-4 flex items-center gap-2 rounded border border-[#222222] bg-[#0b0b0b] px-3 py-2 text-xs">
            <span className="h-2 w-2 rounded-full bg-[#00df8f] shadow-[0_0_6px_#00df8f]" />
            <span className="font-mono text-[11px] font-medium text-[#a5a5a5]">
              Locked Scope: <strong className="text-[#f7f7f7]">HS 8112 → HS 8542</strong>
            </span>
          </div>

          {/* Navigation Views */}
          <div className="mt-6">
            <h2 className="text-[10px] font-bold tracking-widest text-[#666666] uppercase">
              NAVIGATION VIEWS
            </h2>
            <nav className="mt-2 space-y-1.5" aria-label="Main Navigation">
              {navItems.map((item) => {
                const isActive = currentView === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      onSelectView(item.id);
                      onCloseMobile();
                    }}
                    className={`flex w-full items-center justify-between rounded-md border px-3 py-2.5 text-left text-xs transition-all ${
                      isActive
                        ? 'border-[#555555] bg-[#151515] font-semibold text-[#f7f7f7] shadow-[0_0_12px_rgba(255,255,255,0.04)]'
                        : 'border-transparent text-[#a5a5a5] hover:border-[#222222] hover:bg-[#0c0c0c] hover:text-[#f7f7f7]'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <span className={isActive ? 'text-[#00c8ff]' : 'text-[#666666]'}>
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </div>
                    {isActive && (
                      <span
                        className="h-1.5 w-1.5 rounded-full bg-[#00c8ff] shadow-[0_0_8px_#00c8ff]"
                        aria-hidden="true"
                      />
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Target OEM Scope */}
          <div className="mt-6 border-t border-[#1a1a1a] pt-5">
            <label
              htmlFor="oem-selector"
              className="text-[10px] font-bold tracking-widest text-[#666666] uppercase"
            >
              TARGET OEM SCOPE
            </label>
            <div className="relative mt-2">
              <select
                id="oem-selector"
                value={selectedOEMKey}
                onChange={(e) => onSelectOEM(e.target.value as OEMKey)}
                className="w-full appearance-none rounded border border-[#222222] bg-[#0b0b0b] px-3 py-2 text-xs font-medium text-[#f7f7f7] focus:border-[#00c8ff] focus:outline-none cursor-pointer"
              >
                {Object.values(OEM_PROFILES).map((prof) => (
                  <option key={prof.id} value={prof.id}>
                    {prof.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-2.5 top-2.5 h-3.5 w-3.5 text-[#666666]" />
            </div>

            {/* Market share & dependency display */}
            <div className="mt-2.5 rounded bg-[#0b0b0b] p-2 border border-[#1f1f1f] text-[11px] text-[#a5a5a5] space-y-1">
              <div className="flex justify-between">
                <span>SIAM FY24 Share:</span>
                <span className="font-mono font-semibold text-[#f7f7f7]">
                  {currentOEM.marketSharePct}%
                </span>
              </div>
              <div className="flex justify-between">
                <span>Chain Dependency:</span>
                <span className="font-mono font-semibold text-[#00c8ff]">
                  {currentOEM.dependencyRatioPct}%
                </span>
              </div>
            </div>
          </div>

          {/* Extraction Engine */}
          <div className="mt-6 border-t border-[#1a1a1a] pt-5">
            <h2 className="text-[10px] font-bold tracking-widest text-[#666666] uppercase">
              EXTRACTION ENGINE
            </h2>
            <div className="mt-2 space-y-1.5">
              <button
                type="button"
                onClick={() => onSelectEngine('fast')}
                className={`flex w-full items-center justify-between rounded border px-2.5 py-2 text-xs transition ${
                  extractionEngine === 'fast'
                    ? 'border-[#00df8f]/50 bg-[#00df8f]/10 text-[#00df8f] font-semibold'
                    : 'border-[#1e1e1e] bg-[#0b0b0b] text-[#a5a5a5] hover:border-[#333333]'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Cpu className="h-3.5 w-3.5" />
                  <span>Fast Deterministic Parser</span>
                </div>
                {extractionEngine === 'fast' && <span className="h-1.5 w-1.5 rounded-full bg-[#00df8f]" />}
              </button>

              <button
                type="button"
                onClick={() => onSelectEngine('slm')}
                className={`flex w-full items-center justify-between rounded border px-2.5 py-2 text-xs transition ${
                  extractionEngine === 'slm'
                    ? 'border-[#00c8ff]/50 bg-[#00c8ff]/10 text-[#00c8ff] font-semibold'
                    : 'border-[#1e1e1e] bg-[#0b0b0b] text-[#a5a5a5] hover:border-[#333333]'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Cpu className="h-3.5 w-3.5" />
                  <span>Local SLM (Qwen2.5-0.5B)</span>
                </div>
                {extractionEngine === 'slm' && <span className="h-1.5 w-1.5 rounded-full bg-[#00c8ff]" />}
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar Footer: GraphRAG status & Settings popover trigger */}
        <div className="border-t border-[#1a1a1a] p-4 bg-[#070707] space-y-3">
          <div className="rounded border border-[#1e1e1e] bg-[#0c0c0c] p-2.5 text-xs">
            <div className="flex items-center gap-2 font-medium text-[#f7f7f7]">
              <Layers className="h-3.5 w-3.5 text-[#00df8f]" />
              <span>GraphRAG Grounding</span>
            </div>
            <div className="mt-1 flex items-center justify-between text-[11px] text-[#666666]">
              <span>Coverage:</span>
              <span className="font-mono text-[#a5a5a5]">30 Nodes · 69 Edges</span>
            </div>
          </div>

          <button
            onClick={onOpenSettings}
            className="flex w-full items-center justify-center gap-2 rounded border border-[#222222] bg-[#101010] py-1.5 text-xs font-medium text-[#a5a5a5] hover:border-[#3a3a3a] hover:bg-[#151515] hover:text-[#f7f7f7] transition"
          >
            <Settings className="h-3.5 w-3.5" />
            <span>Telemetry Settings</span>
          </button>
        </div>
      </aside>
    </>
  );
};
