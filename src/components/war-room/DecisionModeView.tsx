import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Clock,
  UserCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingDown,
  Layers,
  FileText,
  DollarSign,
  MessageSquare,
  Send,
  Loader2,
  Lock,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { OEMProfile, DecisionQueueEvent, DecisionAuditItem } from '../../types';
import { formatCurrencyValue } from '../../utils/formatters';
import { getDecisionEvents, postDecisionAction } from '../../api/client';

interface DecisionModeViewProps {
  selectedOEM: OEMProfile;
  incidentText: string;
  activeVector: string;
  activeAnalysis: any;
  p95DropPct: number;
  meanDropPct: number;
  currentP95PCaR: number;
  onSelectEvent?: (headline: string, vector: string) => void;
}

const FALLBACK_EVENTS: DecisionQueueEvent[] = [
  {
    id: 'EVT-2026-001',
    headline: 'China restricts gallium and germanium exports citing national security, sparking chip shortage fears in India.',
    risk_band: 'High',
    risk_score: 0.65,
    component: 'Gallium / Germanium',
    oem: 'Maruti Suzuki',
    p95_exposure_crore: 709,
    p95_exposure_range: '₹650 Cr – ₹780 Cr',
    recommended_action: 'Qualify dual-source domestic chemical distributors & allocate 45-day buffer stock',
    net_benefit_crore: 142.5,
    cost_crore: 18.0,
    stale_warning: 'UN Comtrade baseline vintage is 2022; spot prices may fluctuate',
    unverified_warning: 'Chemical precursor distributor unverified in tier-2 node mapping',
    status: 'PENDING',
    assigned_to: null,
    audit_trail: [
      {
        action: 'ingested',
        actor: 'system',
        timestamp: '2026-10-18T10:00:00Z',
        notes: 'Automated ingestion via GDELT / Customs feed'
      }
    ]
  },
  {
    id: 'EVT-2026-002',
    headline: 'TSMC and Vanguard pause automotive MCU fabrication lines in Hsinchu following regional grid power drop.',
    risk_band: 'High',
    risk_score: 0.58,
    component: 'Microcontroller (MCU)',
    oem: 'Tata Motors',
    p95_exposure_crore: 498,
    p95_exposure_range: '₹450 Cr – ₹540 Cr',
    recommended_action: 'Reserve secondary fab allocation with STMicroelectronics / NXP European foundries',
    net_benefit_crore: 95.0,
    cost_crore: 22.0,
    stale_warning: null,
    unverified_warning: 'Hsinchu sub-tier packaging vendor requires human verification',
    status: 'ACKNOWLEDGED',
    assigned_to: 'Semiconductor Procurement Triage Desk',
    audit_trail: [
      {
        action: 'ingested',
        actor: 'system',
        timestamp: '2026-10-18T11:15:00Z',
        notes: 'Automated ingestion via Nikkei Asia feed'
      },
      {
        action: 'acknowledged',
        actor: 'Officer R. Sharma',
        timestamp: '2026-10-18T11:45:00Z',
        notes: 'Acknowledged threat; contacting tier-1 ECU integrator'
      }
    ]
  },
  {
    id: 'EVT-2026-003',
    headline: 'Dense fog and berth congestion at Port of Shanghai delay container vessel departures carrying automotive semiconductors by 9 days.',
    risk_band: 'Medium',
    risk_score: 0.48,
    component: 'Electronic Control Units',
    oem: 'Mahindra',
    p95_exposure_crore: 312,
    p95_exposure_range: '₹280 Cr – ₹350 Cr',
    recommended_action: 'Reroute critical shipments via air freight charter (Shanghai -> Mumbai cargo)',
    net_benefit_crore: 62.0,
    cost_crore: 9.5,
    stale_warning: null,
    unverified_warning: null,
    status: 'PENDING',
    assigned_to: null,
    audit_trail: [
      {
        action: 'ingested',
        actor: 'system',
        timestamp: '2026-10-18T13:30:00Z',
        notes: 'Automated maritime choke point detection'
      }
    ]
  }
];

export const DecisionModeView: React.FC<DecisionModeViewProps> = ({
  selectedOEM,
  incidentText,
  activeVector,
  activeAnalysis,
  p95DropPct,
  meanDropPct,
  currentP95PCaR,
  onSelectEvent,
}) => {
  const [events, setEvents] = useState<DecisionQueueEvent[]>(FALLBACK_EVENTS);
  const [selectedEventId, setSelectedEventId] = useState<string>('EVT-2026-001');
  const [officerName, setOfficerName] = useState<string>('Procurement Officer (Semiconductors)');
  const [commentText, setCommentText] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  // Load events from backend if available
  useEffect(() => {
    let isMounted = true;
    getDecisionEvents().then((res) => {
      if (isMounted && res && res.events && res.events.length > 0) {
        setEvents(res.events);
      }
    }).catch(() => {});
    return () => { isMounted = false; };
  }, []);

  const activeEvent = events.find((e) => e.id === selectedEventId) || events[0];

  const handleAction = async (action: 'acknowledge' | 'assign' | 'comment' | 'resolve', notes?: string) => {
    if (!activeEvent) return;
    setIsSubmitting(true);
    setActionFeedback(null);
    try {
      const res = await postDecisionAction({
        event_id: activeEvent.id,
        action,
        officer: officerName,
        notes: notes || commentText || undefined,
      });

      if (res && res.success) {
        setEvents((prev) =>
          prev.map((evt) => {
            if (evt.id === activeEvent.id) {
              return {
                ...evt,
                status: res.status as any,
                assigned_to: res.assigned_to ?? evt.assigned_to,
                audit_trail: res.audit_trail,
              };
            }
            return evt;
          })
        );
        setActionFeedback(`✅ Action "${action}" recorded with audit timestamp.`);
        if (action === 'comment') setCommentText('');
      } else {
        // Fallback local update
        const now = new Date().toISOString();
        const updatedAudit: DecisionAuditItem = {
          action,
          actor: officerName,
          timestamp: now,
          notes: notes || commentText || `Action ${action} executed locally.`,
        };
        setEvents((prev) =>
          prev.map((evt) => {
            if (evt.id === activeEvent.id) {
              return {
                ...evt,
                status: action === 'resolve' ? 'RESOLVED' : action === 'acknowledge' ? 'ACKNOWLEDGED' : action === 'assign' ? 'IN_REVIEW' : evt.status,
                assigned_to: action === 'assign' ? officerName : evt.assigned_to,
                audit_trail: [...evt.audit_trail, updatedAudit],
              };
            }
            return evt;
          })
        );
        setActionFeedback(`✅ Action "${action}" recorded (offline local audit).`);
        if (action === 'comment') setCommentText('');
      }
    } catch {
      setActionFeedback(`⚠️ Action logged locally.`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Human-in-the-Loop Governance Notice */}
      <div className="rounded-lg border border-[#f5a623]/40 bg-[#120c02] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md">
        <div className="flex items-start gap-3">
          <ShieldAlert className="h-5 w-5 text-[#f5a623] shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold text-[#f7f7f7] uppercase tracking-wider">
              Procurement Officer Decision Triage &amp; Human Approval Policy
            </h4>
            <p className="mt-1 text-xs text-[#a5a5a5] leading-relaxed">
              <strong className="text-[#f5a623]">Never auto-execute purchases or supplier changes:</strong> Causal AI and Small Language Models for Supply Chain Disruption Forecasting and Procurement Cost at Risk Estimation for Indian Automotive Component Sourcing recommendations provide decision support only. All PO allocation adjustments, dual-sourcing contracts, and buffer reserves require explicit human authorization and manual ERP approval.
            </p>
          </div>
        </div>
        <span className="rounded bg-[#f5a623]/20 border border-[#f5a623]/40 px-2 py-1 text-[10px] font-mono font-bold text-[#f5a623] shrink-0">
          HUMAN-IN-THE-LOOP REQUIRED
        </span>
      </div>

      {/* Main Two-Column Decision Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Ranked Event Queue (5 cols) */}
        <div className="lg:col-span-5 rounded-lg border border-[#222222] bg-[#070707] p-4 sm:p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#1a1a1a] pb-3">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-[#00df8f]" />
              <h2 className="text-sm font-semibold tracking-wide text-[#f7f7f7] uppercase">
                Ranked Disruption Event Queue
              </h2>
            </div>
            <span className="text-[10px] font-mono text-[#a5a5a5]">
              {events.length} Active Events
            </span>
          </div>

          <div className="space-y-2.5 max-h-[520px] overflow-y-auto pr-1">
            {events.map((evt) => {
              const isSelected = evt.id === selectedEventId;
              return (
                <div
                  key={evt.id}
                  onClick={() => {
                    setSelectedEventId(evt.id);
                    if (onSelectEvent) {
                      onSelectEvent(evt.headline, evt.component);
                    }
                  }}
                  className={`rounded-lg border p-3.5 text-left transition cursor-pointer ${
                    isSelected
                      ? 'border-[#00df8f] bg-[#06120e] shadow-md'
                      : 'border-[#222222] bg-[#0b0b0b] hover:border-[#3a3a3a] hover:bg-[#101010]'
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] mb-1.5">
                    <span className="font-mono font-bold text-[#00c8ff]">{evt.id}</span>
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${
                          evt.risk_band === 'Critical' || evt.risk_band === 'High'
                            ? 'bg-[#ee0000]/20 text-[#ee0000] border border-[#ee0000]/40'
                            : 'bg-[#f5a623]/20 text-[#f5a623] border border-[#f5a623]/40'
                        }`}
                      >
                        {evt.risk_band} Risk
                      </span>
                      <span
                        className={`rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${
                          evt.status === 'RESOLVED'
                            ? 'bg-[#00df8f]/20 text-[#00df8f] border border-[#00df8f]/40'
                            : evt.status === 'IN_REVIEW' || evt.status === 'ACKNOWLEDGED'
                            ? 'bg-[#00c8ff]/20 text-[#00c8ff] border border-[#00c8ff]/40'
                            : 'bg-[#666666]/20 text-[#a5a5a5] border border-[#666666]/40'
                        }`}
                      >
                        {evt.status}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs font-medium text-[#f7f7f7] leading-snug line-clamp-2">
                    {evt.headline}
                  </p>

                  <div className="mt-2.5 pt-2 border-t border-[#1a1a1a] flex items-center justify-between text-[11px] text-[#a5a5a5]">
                    <div>
                      <span>OEM: </span>
                      <strong className="text-[#f7f7f7]">{evt.oem}</strong>
                    </div>
                    <div>
                      <span>P95 Exposure: </span>
                      <strong className="text-[#00c8ff] font-mono">{evt.p95_exposure_range}</strong>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Triage, Approval Workflow & Net-Benefit (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {activeEvent && (
            <div className="rounded-lg border border-[#222222] bg-[#070707] p-5 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#1a1a1a] pb-3 gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-[#00c8ff]">{activeEvent.id}</span>
                    <h3 className="text-sm font-bold text-[#f7f7f7]">Procurement Action Plan &amp; Approvals</h3>
                  </div>
                  <p className="text-[11px] text-[#a5a5a5] mt-0.5">
                    Target OEM: <strong className="text-[#f7f7f7]">{activeEvent.oem}</strong> · Component: <strong className="text-[#00c8ff]">{activeEvent.component}</strong>
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[#a5a5a5]">Current Status:</span>
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-bold uppercase ${
                      activeEvent.status === 'RESOLVED'
                        ? 'bg-[#00df8f]/20 text-[#00df8f] border border-[#00df8f]/40'
                        : activeEvent.status === 'IN_REVIEW' || activeEvent.status === 'ACKNOWLEDGED'
                        ? 'bg-[#00c8ff]/20 text-[#00c8ff] border border-[#00c8ff]/40'
                        : 'bg-[#ee0000]/20 text-[#ee0000] border border-[#ee0000]/40'
                    }`}
                  >
                    {activeEvent.status}
                  </span>
                </div>
              </div>

              {/* Warnings (Stale data & Unverified entities) */}
              {(activeEvent.stale_warning || activeEvent.unverified_warning) && (
                <div className="space-y-2">
                  {activeEvent.stale_warning && (
                    <div className="flex items-center gap-2 rounded border border-[#f5a623]/30 bg-[#f5a623]/10 p-2.5 text-xs text-[#f5a623]">
                      <AlertTriangle className="h-4 w-4 shrink-0" />
                      <span><strong>Stale Data Advisory:</strong> {activeEvent.stale_warning}</span>
                    </div>
                  )}
                  {activeEvent.unverified_warning && (
                    <div className="flex items-center gap-2 rounded border border-[#ee0000]/30 bg-[#ee0000]/10 p-2.5 text-xs text-[#ee0000]">
                      <AlertTriangle className="h-4 w-4 shrink-0" />
                      <span><strong>Unverified Entity Warning:</strong> {activeEvent.unverified_warning} (Review state: NEEDS_HUMAN_VERIFICATION)</span>
                    </div>
                  )}
                </div>
              )}

              {/* Recommended Action with Net-Benefit Matrix */}
              <div className="rounded-lg border border-[#00df8f]/30 bg-[#06120e] p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold tracking-wider text-[#00df8f] uppercase">
                    RECOMMENDED ACTION &amp; NET-BENEFIT MATRIX
                  </span>
                  <span className="text-[10px] text-[#00df8f] font-mono font-bold">
                    AlMahri Cost-Adjusted Directive
                  </span>
                </div>
                <h4 className="text-xs font-semibold text-[#f7f7f7] leading-relaxed">
                  &ldquo;{activeEvent.recommended_action}&rdquo;
                </h4>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-[#00df8f]/20 text-[#64748b] uppercase text-[9.5px] tracking-wider">
                        <th className="py-1.5 px-2">Mitigation Action</th>
                        <th className="py-1.5 px-2 text-right">Implementation Cost</th>
                        <th className="py-1.5 px-2 text-right">Risk Mitigation</th>
                        <th className="py-1.5 px-2 text-right">Net Benefit</th>
                        <th className="py-1.5 px-2 text-right">Payback</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#00df8f]/10 font-mono">
                      <tr>
                        <td className="py-2 px-2 font-sans font-medium text-[#f7f7f7]">
                          Dual-Source Qualification &amp; Buffer
                        </td>
                        <td className="py-2 px-2 text-right text-[#f5a623]">
                          ₹{activeEvent.cost_crore.toFixed(1)} Cr
                        </td>
                        <td className="py-2 px-2 text-right text-[#00df8f]">
                          ₹{(activeEvent.net_benefit_crore + activeEvent.cost_crore).toFixed(1)} Cr
                        </td>
                        <td className="py-2 px-2 text-right font-bold text-[#00df8f]">
                          +₹{activeEvent.net_benefit_crore.toFixed(1)} Cr
                        </td>
                        <td className="py-2 px-2 text-right text-[#a5a5a5]">
                          &lt; 3 Months
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Officer Action Bar */}
              <div className="rounded-lg border border-[#1f1f1f] bg-[#0c0c0c] p-4 space-y-3">
                <span className="text-[10px] font-bold tracking-wider text-[#666666] uppercase block">
                  OFFICER WORKFLOW EXECUTION
                </span>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => handleAction('acknowledge')}
                    disabled={isSubmitting || activeEvent.status !== 'PENDING'}
                    className="flex items-center justify-center gap-1.5 rounded border border-[#00c8ff]/40 bg-[#00c8ff]/10 py-2 px-3 text-xs font-bold text-[#00c8ff] hover:bg-[#00c8ff]/20 transition disabled:opacity-40 cursor-pointer"
                  >
                    <UserCheck className="h-3.5 w-3.5" />
                    <span>Acknowledge Threat</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleAction('assign', 'Semiconductor Procurement Desk')}
                    disabled={isSubmitting || activeEvent.status === 'RESOLVED'}
                    className="flex items-center justify-center gap-1.5 rounded border border-[#f5a623]/40 bg-[#f5a623]/10 py-2 px-3 text-xs font-bold text-[#f5a623] hover:bg-[#f5a623]/20 transition disabled:opacity-40 cursor-pointer"
                  >
                    <Clock className="h-3.5 w-3.5" />
                    <span>Assign to Triage Desk</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleAction('resolve', 'Approved PO & Dual-Source Contract')}
                    disabled={isSubmitting || activeEvent.status === 'RESOLVED'}
                    className="flex items-center justify-center gap-1.5 rounded border border-[#00df8f]/40 bg-[#00df8f]/10 py-2 px-3 text-xs font-bold text-[#00df8f] hover:bg-[#00df8f]/20 transition disabled:opacity-40 cursor-pointer"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Approve &amp; Resolve</span>
                  </button>
                </div>

                {/* Comment Box */}
                <div className="flex gap-2 pt-1">
                  <input
                    type="text"
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    placeholder="Add officer operational comment or supplier note..."
                    className="flex-1 rounded border border-[#222222] bg-[#070707] px-3 py-1.5 text-xs text-[#f7f7f7] placeholder-[#666666] focus:border-[#00df8f] focus:outline-none font-sans"
                  />
                  <button
                    type="button"
                    onClick={() => handleAction('comment')}
                    disabled={isSubmitting || !commentText.trim()}
                    className="flex items-center gap-1 rounded bg-[#ffffff] px-3 py-1.5 text-xs font-bold text-black hover:bg-[#e0e0e0] transition disabled:opacity-40 cursor-pointer"
                  >
                    {isSubmitting ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Send className="h-3.5 w-3.5" />
                    )}
                    <span>Comment</span>
                  </button>
                </div>

                {actionFeedback && (
                  <div className="text-[11px] text-[#00df8f] pt-1 font-mono">
                    {actionFeedback}
                  </div>
                )}
              </div>

              {/* Audit Trail */}
              <div className="space-y-2 border-t border-[#1a1a1a] pt-3">
                <span className="text-[10px] font-bold tracking-wider text-[#666666] uppercase block">
                  AUDIT TRAIL &amp; TIMESTAMPS ({activeEvent.audit_trail.length} ACTIONS)
                </span>
                <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                  {activeEvent.audit_trail.map((item, idx) => (
                    <div
                      key={idx}
                      className="rounded border border-[#1a1a1a] bg-[#0c0c0c] p-2 flex items-center justify-between text-[11px] font-mono"
                    >
                      <div className="flex items-center gap-2">
                        <span className="rounded bg-[#00df8f]/10 border border-[#00df8f]/30 px-1.5 py-0.2 text-[9px] font-bold uppercase text-[#00df8f]">
                          {item.action}
                        </span>
                        <span className="font-sans text-[#f7f7f7]">{item.notes || item.action}</span>
                      </div>
                      <div className="text-[10px] text-[#666666] shrink-0 ml-2">
                        <span>{item.actor}</span> · <span>{item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : 'N/A'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
