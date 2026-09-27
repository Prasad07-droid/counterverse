import React, { useState } from 'react';
import { Menu } from 'lucide-react';
import { NavView, OEMKey, ExtractionEngine } from '../../types';
import { OEM_PROFILES } from '../../data/mockData';
import { Sidebar } from './Sidebar';
import { TopScopeBar } from './TopScopeBar';
import { SettingsModal } from '../common/SettingsModal';

interface ShellProps {
  currentView: NavView;
  onSelectView: (view: NavView) => void;
  selectedOEMKey: OEMKey;
  onSelectOEM: (key: OEMKey) => void;
  extractionEngine: ExtractionEngine;
  onSelectEngine: (engine: ExtractionEngine) => void;
  simulationSeed: number;
  onResetSeed: () => void;
  children: React.ReactNode;
}

export const Shell: React.FC<ShellProps> = ({
  currentView,
  onSelectView,
  selectedOEMKey,
  onSelectOEM,
  extractionEngine,
  onSelectEngine,
  simulationSeed,
  onResetSeed,
  children,
}) => {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [simulationSpeed, setSimulationSpeed] = useState<'realtime' | 'turbo'>('realtime');

  const selectedOEM = OEM_PROFILES[selectedOEMKey];

  return (
    <div className="min-h-screen bg-black text-[#f7f7f7] cv-grid-bg flex flex-col lg:flex-row">
      {/* Sidebar (Desktop fixed, Mobile drawer) */}
      <Sidebar
        currentView={currentView}
        onSelectView={onSelectView}
        selectedOEMKey={selectedOEMKey}
        onSelectOEM={onSelectOEM}
        extractionEngine={extractionEngine}
        onSelectEngine={onSelectEngine}
        onOpenSettings={() => setIsSettingsOpen(true)}
        isOpenMobile={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile Header Bar (Only visible < lg) */}
        <div className="flex items-center justify-between border-b border-[#222222] bg-[#070707] px-4 py-3 lg:hidden">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded bg-[#f7f7f7]">
              <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 fill-black">
                <polygon points="12 4 21 20 3 20" />
              </svg>
            </div>
            <span className="font-bold text-sm text-[#f7f7f7] tracking-tight">CounterVerse</span>
          </div>

          <button
            onClick={() => setIsMobileSidebarOpen(true)}
            className="rounded p-1.5 text-[#a5a5a5] hover:bg-[#151515] hover:text-[#f7f7f7]"
            aria-label="Open mobile navigation"
            aria-expanded={isMobileSidebarOpen}
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>

        {/* Sticky Top Scope Bar */}
        <TopScopeBar selectedOEM={selectedOEM} />

        {/* Viewport Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        simulationSeed={simulationSeed}
        onResetSeed={onResetSeed}
        simulationSpeed={simulationSpeed}
        onToggleSpeed={() => setSimulationSpeed((s) => (s === 'realtime' ? 'turbo' : 'realtime'))}
      />
    </div>
  );
};
