import React, { useEffect, useRef } from 'react';
import { X, Sliders, RefreshCw, Eye, ShieldCheck } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  simulationSeed: number;
  onResetSeed: () => void;
  simulationSpeed: 'realtime' | 'turbo';
  onToggleSpeed: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  simulationSeed,
  onResetSeed,
  simulationSpeed,
  onToggleSpeed,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="settings-title"
    >
      <div
        ref={modalRef}
        className="w-full max-w-md rounded-lg border border-[#222222] bg-[#0b0b0b] p-6 shadow-2xl transition-all"
      >
        <div className="flex items-center justify-between border-b border-[#222222] pb-4">
          <div className="flex items-center gap-2">
            <Sliders className="h-4 w-4 text-[#00c8ff]" />
            <h2 id="settings-title" className="text-sm font-semibold tracking-wide text-[#f7f7f7] uppercase">
              System & Telemetry Settings
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-[#a5a5a5] hover:bg-[#151515] hover:text-[#f7f7f7] transition"
            aria-label="Close settings"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-5 space-y-5 text-xs text-[#a5a5a5]">
          <div>
            <div className="flex items-center justify-between">
              <span className="font-mono text-[#f7f7f7]">Stochastic Simulation Seed</span>
              <span className="rounded bg-[#151515] px-2 py-0.5 font-mono text-[#00c8ff] border border-[#222222]">
                {simulationSeed}
              </span>
            </div>
            <p className="mt-1 text-[11px] text-[#666666]">
              Deterministic pseudorandom generator seed. Fixed seed ensures 100% reproducible scenario results.
            </p>
            <button
              onClick={onResetSeed}
              className="mt-2.5 inline-flex items-center gap-1.5 rounded border border-[#222222] bg-[#101010] px-3 py-1.5 text-xs font-medium text-[#f7f7f7] hover:border-[#3a3a3a] hover:bg-[#151515] transition"
            >
              <RefreshCw className="h-3 w-3 text-[#a5a5a5]" />
              Reset Deterministic Seed
            </button>
          </div>

          <div className="border-t border-[#222222] pt-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[#f7f7f7]">Flow Particle Velocity</span>
              <button
                onClick={onToggleSpeed}
                className="rounded border border-[#222222] bg-[#151515] px-2.5 py-1 font-mono text-xs text-[#00c8ff] hover:border-[#3a3a3a] transition"
              >
                {simulationSpeed === 'realtime' ? '1.0x Realtime' : '2.5x Turbo'}
              </button>
            </div>
            <p className="mt-1 text-[11px] text-[#666666]">
              Controls SVG particle frequency across active supply chain conduits in War Room view.
            </p>
          </div>

          <div className="border-t border-[#222222] pt-4">
            <div className="flex items-start gap-2">
              <ShieldCheck className="h-4 w-4 text-[#00df8f] shrink-0 mt-0.5" />
              <div>
                <span className="font-medium text-[#f7f7f7]">Deterministic Demo Mode</span>
                <p className="mt-0.5 text-[11px] text-[#666666]">
                  All calculations are executed locally via verified formulas. Zero external network dependency or ungrounded generative hallucination.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end border-t border-[#222222] pt-4">
          <button
            onClick={onClose}
            className="rounded bg-[#f7f7f7] px-4 py-1.5 text-xs font-semibold text-[#000000] hover:bg-[#eaeaea] transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
