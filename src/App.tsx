import React, { useState } from 'react';
import { NavView, OEMKey, ExtractionEngine } from './types';
import { OEM_PROFILES } from './data/mockData';
import { Shell } from './components/layout/Shell';
import { ExecutiveWarRoom } from './components/war-room/ExecutiveWarRoom';
import { FinancialExposureView } from './components/pcar/FinancialExposureView';
import { GovernanceView } from './components/governance/GovernanceView';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<NavView>('war-room');
  const [selectedOEMKey, setSelectedOEMKey] = useState<OEMKey>('maruti');
  const [extractionEngine, setExtractionEngine] = useState<ExtractionEngine>('fast');
  const [simulationSeed, setSimulationSeed] = useState<number>(42);

  const selectedOEM = OEM_PROFILES[selectedOEMKey];

  return (
    <Shell
      currentView={currentView}
      onSelectView={setCurrentView}
      selectedOEMKey={selectedOEMKey}
      onSelectOEM={setSelectedOEMKey}
      extractionEngine={extractionEngine}
      onSelectEngine={setExtractionEngine}
      simulationSeed={simulationSeed}
      onResetSeed={() => setSimulationSeed((s) => s + 1)}
    >
      {currentView === 'war-room' && <ExecutiveWarRoom selectedOEM={selectedOEM} />}
      {currentView === 'financial-exposure' && (
        <FinancialExposureView
          selectedOEM={selectedOEM}
          onSelectOEM={setSelectedOEMKey}
          simulationSeed={simulationSeed}
        />
      )}
      {currentView === 'governance' && <GovernanceView />}
    </Shell>
  );
};

export default App;
