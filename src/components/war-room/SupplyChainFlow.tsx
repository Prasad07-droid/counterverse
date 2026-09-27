import React, { useState } from 'react';
import {
  Activity,
  Play,
  Pause,
  RotateCcw,
  Zap,
  Info,
  X,
  Radio,
  Anchor,
  Cpu,
  Factory,
  Car,
  Package,
  Store
} from 'lucide-react';
import { SupplyChainNode, SupplyChainEdge, RouteStatus } from '../../types';
import { INITIAL_NODES, INITIAL_EDGES } from '../../data/mockData';

interface SupplyChainFlowProps {
  disruptedChoke: string;
}

export const SupplyChainFlow: React.FC<SupplyChainFlowProps> = ({ disruptedChoke }) => {
  const [nodes, setNodes] = useState<SupplyChainNode[]>(INITIAL_NODES);
  const [edges, setEdges] = useState<SupplyChainEdge[]>(INITIAL_EDGES);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [shockActive, setShockActive] = useState<boolean>(false);
  const [shockRadius, setShockRadius] = useState<number>(0);
  const [selectedNode, setSelectedNode] = useState<SupplyChainNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<SupplyChainEdge | null>(null);

  const handleTogglePause = () => {
    setIsPaused(!isPaused);
  };

  const handleTriggerShock = () => {
    if (shockActive) return;
    setShockActive(true);
    setShockRadius(10);

    let r = 10;
    const interval = setInterval(() => {
      r += 24;
      setShockRadius(r);
      if (r > 600) {
        clearInterval(interval);
        setShockActive(false);
        setShockRadius(0);
      }
    }, 25);
  };

  const handleResetView = () => {
    setNodes(INITIAL_NODES);
    setEdges(INITIAL_EDGES);
    setIsPaused(false);
    setShockActive(false);
    setShockRadius(0);
    setSelectedNode(null);
  };

  const getNodeIcon = (category: string) => {
    switch (category) {
      case 'port':
        return <Anchor className="h-3.5 w-3.5" />;
      case 'fab':
        return <Cpu className="h-3.5 w-3.5" />;
      case 'component':
        return <Factory className="h-3.5 w-3.5" />;
      case 'assembly':
        return <Car className="h-3.5 w-3.5" />;
      case 'logistics':
        return <Package className="h-3.5 w-3.5" />;
      case 'retail':
        return <Store className="h-3.5 w-3.5" />;
      default:
        return <Activity className="h-3.5 w-3.5" />;
    }
  };

  const getStatusColor = (status: RouteStatus) => {
    switch (status) {
      case 'optimal':
        return '#00df8f';
      case 'constrained':
        return '#f5a623';
      case 'starved':
        return '#f5a623';
      case 'blocked':
        return '#ee0000';
    }
  };

  return (
    <div className="flex flex-col rounded-lg border border-[#222222] bg-[#111a2e] shadow-xl overflow-hidden">
      {/* Flow Header */}
      <div className="flex flex-col gap-2.5 border-b border-[#222222]/80 bg-[#0d1424] px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[#00c8ff] shadow-[0_0_8px_#00c8ff]" />
            <h2 className="text-sm font-semibold tracking-wide text-[#f7f7f7]">
              Causal Supply Chain Flow
            </h2>
            <span className="rounded border border-[#1787ff]/40 bg-[#1787ff]/10 px-2 py-0.5 text-[10px] font-mono text-[#00c8ff]">
              8 nodes · 9 edges · 60 FPS
            </span>
          </div>
          <p className="mt-0.5 text-xs text-[#a5a5a5]">
            Real-Time Material & Component Flow Simulation across multi-tier corridors
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-1.5 self-start sm:self-auto">
          <button
            onClick={handleTriggerShock}
            disabled={shockActive}
            className={`inline-flex items-center gap-1 rounded border px-2.5 py-1 text-xs font-medium transition ${
              shockActive
                ? 'border-[#ee0000] bg-[#ee0000]/20 text-[#ee0000]'
                : 'border-[#222222] bg-[#151f38] text-[#f7f7f7] hover:border-[#3a3a3a] hover:bg-[#1a2747]'
            }`}
            title="Simulate shock propagation wave"
          >
            <Zap className="h-3 w-3 text-[#ee0000]" />
            <span>Shock Ripple</span>
          </button>

          <button
            onClick={handleTogglePause}
            className="inline-flex items-center gap-1 rounded border border-[#222222] bg-[#151f38] px-2.5 py-1 text-xs font-medium text-[#f7f7f7] hover:border-[#3a3a3a] hover:bg-[#1a2747] transition"
          >
            {isPaused ? <Play className="h-3 w-3 text-[#00df8f]" /> : <Pause className="h-3 w-3 text-[#a5a5a5]" />}
            <span>{isPaused ? 'Resume Flow' : 'Pause Flow'}</span>
          </button>

          <button
            onClick={handleResetView}
            className="inline-flex items-center gap-1 rounded border border-[#222222] bg-[#151f38] px-2 py-1 text-xs font-medium text-[#a5a5a5] hover:border-[#3a3a3a] hover:text-[#f7f7f7] transition"
            title="Reset simulation graph to initial state"
          >
            <RotateCcw className="h-3 w-3" />
            <span className="sr-only sm:not-sr-only">Reset</span>
          </button>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div className="relative w-full overflow-x-auto bg-[#090f1d] min-h-[380px] select-none">
        <svg
          viewBox="0 0 920 400"
          className="w-full min-w-[700px] h-[390px] block"
          role="img"
          aria-label="Causal supply chain flow diagram"
        >
          <defs>
            {/* Glow filter */}
            <filter id="particle-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>

            {/* Shock Ripple Gradient */}
            <radialGradient id="shock-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ee0000" stopOpacity="0.4" />
              <stop offset="70%" stopColor="#ee0000" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#ee0000" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Background Conduit Base (Dark tracks) */}
          {edges.map((edge) => (
            <path
              key={`base-${edge.id}`}
              d={edge.path}
              fill="none"
              stroke="#131c30"
              strokeWidth="5"
              strokeLinecap="round"
            />
          ))}

          {/* Active Status Conduits */}
          {edges.map((edge) => {
            const isBlocked = edge.status === 'blocked';
            const isConstrained = edge.status === 'constrained';
            const isStarved = edge.status === 'starved';

            return (
              <g key={`edge-${edge.id}`}>
                <path
                  id={edge.id}
                  d={edge.path}
                  fill="none"
                  stroke={
                    isBlocked ? '#ee0000' : isConstrained || isStarved ? '#f5a623' : '#00c8ff'
                  }
                  strokeWidth={selectedEdge?.id === edge.id ? '4' : isBlocked ? '2.5' : '3'}
                  strokeDasharray={isBlocked ? '6,6' : undefined}
                  strokeOpacity={isBlocked ? 0.9 : 0.8}
                  strokeLinecap="round"
                  className="cursor-pointer transition-all hover:stroke-opacity-100 hover:stroke-[4px]"
                  onClick={() => setSelectedEdge(edge)}
                >
                  <title>{`${edge.status} - ${edge.flowPct}%`}</title>
                </path>

                {/* Animated Material Particles (Only on non-blocked routes when not paused) */}
                {!isBlocked && !isPaused && (
                  <>
                    <circle r="4" fill="#00df8f" filter="url(#particle-glow)">
                      <animateMotion
                        dur={isConstrained || isStarved ? '4.8s' : '2.0s'}
                        repeatCount="indefinite"
                      >
                        <mpath href={`#${edge.id}`} />
                      </animateMotion>
                    </circle>
                    <circle r="3.5" fill="#00c8ff" filter="url(#particle-glow)">
                      <animateMotion
                        dur={isConstrained || isStarved ? '4.8s' : '2.0s'}
                        begin={isConstrained || isStarved ? '2.4s' : '1.0s'}
                        repeatCount="indefinite"
                      >
                        <mpath href={`#${edge.id}`} />
                      </animateMotion>
                    </circle>
                  </>
                )}

                {/* Midpoint flow badge */}
                <g
                  transform={`translate(${edge.midX - 30}, ${edge.midY - 10})`}
                  className="cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => setSelectedEdge(edge)}
                >
                  <rect
                    width="60"
                    height="18"
                    rx="4"
                    fill="#080e1a"
                    stroke={getStatusColor(edge.status)}
                    strokeWidth="1"
                    strokeOpacity="0.6"
                  />
                  <text
                    x="30"
                    y="13"
                    textAnchor="middle"
                    fill={getStatusColor(edge.status)}
                    fontFamily="Geist Mono, monospace"
                    fontSize="9.5"
                    fontWeight="600"
                  >
                    {edge.flowPct}% Flow
                  </text>
                </g>
              </g>
            );
          })}

          {/* Shock Ripple Wave Effect */}
          {shockActive && (
            <circle
              cx="100"
              cy="315"
              r={shockRadius}
              fill="none"
              stroke="#ee0000"
              strokeWidth="3.5"
              strokeOpacity={Math.max(0, 1 - shockRadius / 600)}
            />
          )}

          {/* Nodes Layer */}
          {nodes.map((node) => {
            const isBlocked = node.status === 'blocked';
            const isStarved = node.status === 'starved';
            const isSelected = selectedNode?.id === node.id;

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => setSelectedNode(node)}
                className="group cursor-pointer select-none"
              >
                {/* Fixed invisible hit-area circle to prevent hover flickering */}
                <circle r="34" fill="transparent" pointerEvents="all" />

                {/* Warning Hazard Beacon on Blocked Choke */}
                {isBlocked && (
                  <circle
                    r="34"
                    fill="none"
                    stroke="#ee0000"
                    strokeWidth="1.8"
                    strokeDasharray="4,4"
                  >
                    <animate
                      attributeName="r"
                      values="30;35;30"
                      dur="2.2s"
                      repeatCount="indefinite"
                    />
                    <animate
                      attributeName="stroke-opacity"
                      values="0.9;0.25;0.9"
                      dur="2.2s"
                      repeatCount="indefinite"
                    />
                  </circle>
                )}

                {/* Node Outer Ring */}
                <circle
                  r={isSelected ? 26 : 24}
                  fill="#0b1220"
                  stroke={
                    isSelected
                      ? '#ffffff'
                      : isBlocked
                      ? '#ee0000'
                      : isStarved
                      ? '#f5a623'
                      : '#1787ff'
                  }
                  strokeWidth={isSelected ? '2.5' : '1.8'}
                  className="transition-all duration-150 group-hover:stroke-white group-hover:stroke-[2.5px]"
                  style={{
                    filter: isSelected
                      ? 'drop-shadow(0 0 8px rgba(0, 200, 255, 0.7))'
                      : undefined
                  }}
                />

                {/* Node Center Icon Wrapper */}
                <foreignObject x="-10" y="-10" width="20" height="20" className="pointer-events-none">
                  <div
                    className={`flex h-full w-full items-center justify-center ${
                      isBlocked ? 'text-[#ee0000]' : isStarved ? 'text-[#f5a623]' : 'text-[#00c8ff]'
                    }`}
                  >
                    {getNodeIcon(node.tierCategory)}
                  </div>
                </foreignObject>

                {/* Status Indicator Dot */}
                <circle
                  cx="16"
                  cy="-16"
                  r="4.5"
                  fill={
                    isBlocked
                      ? '#ee0000'
                      : isStarved
                      ? '#f5a623'
                      : node.status === 'constrained'
                      ? '#f5a623'
                      : '#00df8f'
                  }
                  stroke="#0b1220"
                  strokeWidth="1.5"
                />

                {/* Node Label Below */}
                <text
                  y="38"
                  textAnchor="middle"
                  fill="#f7f7f7"
                  fontFamily="Geist, sans-serif"
                  fontSize="11"
                  fontWeight="600"
                >
                  {node.name}
                </text>

                {/* Tier Subtitle */}
                <text
                  y="49"
                  textAnchor="middle"
                  fill="#a5a5a5"
                  fontFamily="Geist, sans-serif"
                  fontSize="8.5"
                >
                  {node.tier}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Selected Node Detail Popover */}
        {selectedNode && (
          <div className="absolute right-4 top-4 z-20 w-72 rounded-lg border border-[#3a3a3a] bg-[#070707]/95 p-4 text-xs shadow-2xl backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-[#222222] pb-2">
              <div className="flex items-center gap-2">
                <Radio className="h-3.5 w-3.5 text-[#00c8ff]" />
                <h3 className="font-semibold text-[#f7f7f7]">{selectedNode.name}</h3>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="rounded p-1 text-[#666666] hover:bg-[#151515] hover:text-[#f7f7f7]"
                aria-label="Close node inspector"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>

            <div className="mt-3 space-y-2 text-[#a5a5a5]">
              <div className="flex justify-between">
                <span>Tier Classification:</span>
                <span className="font-medium text-[#f7f7f7]">{selectedNode.tier}</span>
              </div>
              <div className="flex justify-between">
                <span>Geographic Region:</span>
                <span className="font-medium text-[#f7f7f7]">{selectedNode.country} ({selectedNode.region})</span>
              </div>
              <div className="flex justify-between">
                <span>Current Throughput:</span>
                <span className="font-mono font-semibold text-[#00c8ff]">
                  {selectedNode.throughputPct}% Operational
                </span>
              </div>
              <div className="flex justify-between">
                <span>Import Dependency:</span>
                <span className="font-mono font-semibold text-[#f5a623]">
                  {selectedNode.dependencyRatioPct}%
                </span>
              </div>
              <div className="flex justify-between border-t border-[#222222] pt-2">
                <span>Node Health:</span>
                <span
                  className="rounded px-2 py-0.5 text-[10px] font-bold uppercase"
                  style={{
                    backgroundColor: `${getStatusColor(selectedNode.status)}18`,
                    color: getStatusColor(selectedNode.status),
                    border: `1px solid ${getStatusColor(selectedNode.status)}40`,
                  }}
                >
                  {selectedNode.status}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Edge Detail Popover */}
        {selectedEdge && (() => {
          const sourceNode = nodes.find((n) => n.id === selectedEdge.source);
          const targetNode = nodes.find((n) => n.id === selectedEdge.target);
          return (
            <div className="absolute left-4 top-4 z-20 w-80 rounded-lg border border-[#3a3a3a] bg-[#070707]/95 p-4 text-xs shadow-2xl backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-[#222222] pb-2">
                <div className="flex items-center gap-2">
                  <Radio className="h-3.5 w-3.5 text-[#00c8ff]" />
                  <h3 className="font-semibold text-[#f7f7f7]">Corridor Telemetry</h3>
                </div>
                <button
                  onClick={() => setSelectedEdge(null)}
                  className="rounded p-1 text-[#666666] hover:bg-[#151515] hover:text-[#f7f7f7]"
                  aria-label="Close edge inspector"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
              <div className="mt-3 space-y-2 text-[#a5a5a5]">
                <div className="flex justify-between">
                  <span>Routing Corridor:</span>
                  <span className="font-medium text-[#f7f7f7]">
                    {sourceNode?.name || selectedEdge.source} → {targetNode?.name || selectedEdge.target}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Corridor ID:</span>
                  <span className="font-mono text-[#f7f7f7]">{selectedEdge.id}</span>
                </div>
                <div className="flex justify-between">
                  <span>Current Flow Rate:</span>
                  <span className="font-mono font-semibold text-[#00c8ff]">
                    {selectedEdge.flowPct}% Active
                  </span>
                </div>
                <div className="flex justify-between border-t border-[#222222] pt-2">
                  <span>Route Health:</span>
                  <span
                    className="rounded px-2 py-0.5 text-[10px] font-bold uppercase"
                    style={{
                      backgroundColor: `${getStatusColor(selectedEdge.status)}18`,
                      color: getStatusColor(selectedEdge.status),
                      border: `1px solid ${getStatusColor(selectedEdge.status)}40`,
                    }}
                  >
                    {selectedEdge.status}
                  </span>
                </div>
              </div>
            </div>
          );
        })()}
      </div>

      {/* Compact Legend Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-t border-[#222222] bg-[#0b101c] px-4 py-2.5 text-xs text-[#a5a5a5]">
        <div className="flex items-center gap-5 flex-wrap text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-[#00df8f]" />
            <span>Optimal (100% Flow)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-[#f5a623]" />
            <span>Constrained / Starved</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-[#ee0000]" />
            <span>Blocked / Severed (0% Flow)</span>
          </div>
        </div>
        <div className="text-[11px] text-[#666666] font-mono">
          Click any node or route corridor to inspect telemetry
        </div>
      </div>
    </div>
  );
};
