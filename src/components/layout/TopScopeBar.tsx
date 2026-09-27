import React from 'react';
import { Lock, ArrowRight, Database } from 'lucide-react';
import { OEMProfile } from '../../types';
import { formatCurrencyValue } from '../../utils/formatters';
import { MACRO_BASELINE_CRORE } from '../../data/mockData';

interface TopScopeBarProps {
  selectedOEM: OEMProfile;
}

export const TopScopeBar: React.FC<TopScopeBarProps> = ({ selectedOEM }) => {
  return (
    <header className="sticky top-0 z-30 w-full border-b border-[#222222] bg-[#070707]/90 backdrop-blur-md px-4 py-2.5 sm:px-6">
      <div className="flex flex-col gap-2.5 sm:flex-row sm:items-center sm:justify-between text-xs overflow-x-auto no-scrollbar">
        {/* Left: Scope details */}
        <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
          <div className="inline-flex items-center gap-1.5 font-medium text-[#1787ff] text-[11px] tracking-wider uppercase">
            <Lock className="h-3.5 w-3.5 text-[#1787ff]" />
            <span>SCOPE LOCKED</span>
          </div>

          <span className="rounded border border-[#1787ff]/40 bg-[#1787ff]/10 px-2 py-0.5 font-mono text-[11px] font-semibold text-[#00c8ff]">
            HS 8112 → HS 8542
          </span>

          <div className="hidden lg:flex items-center gap-1.5 text-[#a5a5a5] text-[11px]">
            <span>Gallium/Germanium</span>
            <ArrowRight className="h-3 w-3 text-[#666666]" />
            <span>Semiconductor/ICs</span>
            <ArrowRight className="h-3 w-3 text-[#666666]" />
            <span>Automotive ECU</span>
            <ArrowRight className="h-3 w-3 text-[#666666]" />
            <span className="font-semibold text-[#f7f7f7]">{selectedOEM.name}</span>
          </div>
        </div>

        {/* Right: Baselines */}
        <div className="flex items-center gap-3 shrink-0 text-[11px] font-mono">
          <div className="flex items-center gap-1.5 text-[#a5a5a5]">
            <span className="text-[#666666]">Allocated:</span>
            <strong className="text-[#f7f7f7]">
              {formatCurrencyValue(selectedOEM.allocatedBaselineCr, 'INR')}
            </strong>
          </div>

          <span className="text-[#3a3a3a]">|</span>

          <div className="flex items-center gap-1.5 text-[#a5a5a5]" title="UN Comtrade 2022 Audited Full Year HS 8542 Baseline">
            <Database className="h-3 w-3 text-[#666666]" />
            <span className="text-[#666666]">Macro:</span>
            <span className="text-[#a5a5a5]">{formatCurrencyValue(MACRO_BASELINE_CRORE, 'INR')}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
