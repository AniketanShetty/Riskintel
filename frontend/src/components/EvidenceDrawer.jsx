import { ChevronDown, ChevronUp, FileSearch, GitBranch, Layers } from 'lucide-react'

function AdviceTypeBadge({ type }) {
  const map = {
    evidence_based: 'bg-[var(--color-cyan-code)] text-slate-900',
    inferred: 'bg-amber-200 text-amber-900',
    generic: 'bg-slate-700 text-slate-300',
  }
  const label = type ? type.replace('_', ' ') : 'generic'
  return (
    <span className={`text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded ${map[type] || map.generic}`}>
      {label}
    </span>
  )
}

function ThresholdChip({ label, value, highlight = false }) {
  return (
    <div
      className={`px-2.5 py-1 rounded font-mono text-xs ${
        highlight
          ? 'bg-[var(--color-sage)] text-white'
          : 'bg-slate-800 text-slate-200 border border-slate-700'
      }`}
    >
      <span className="text-slate-400 mr-1">{label}</span>
      <span className="font-semibold">{value}</span>
    </div>
  )
}

function RoutingChip({ label, value }) {
  return (
    <div className="px-2.5 py-1 rounded font-mono text-xs bg-slate-800 text-slate-200 border border-slate-700">
      <span className="text-slate-400 mr-1">{label}</span>
      <span className="font-semibold">{value}</span>
    </div>
  )
}

export default function EvidenceDrawer({ factor, response, isOpen, onToggle }) {
  const sources = factor.evidence_sources || []
  const hasThresholds = response.user_type === 'person_a' && response.risk_tier?.threshold_values
  const hasE5Thresholds = response.user_type === 'person_b' && response.readiness?.metadata?.e5_thresholds

  return (
    <div className="border-t border-slate-700">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-2 px-4 sm:px-5 py-3 bg-slate-800 hover:bg-slate-700 transition-colors duration-150 text-[var(--color-cyan-code)] text-xs font-mono uppercase tracking-wider min-w-0"
      >
        <span className="flex items-center gap-2 min-w-0">
          <FileSearch className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate">Evidence Trace</span>
        </span>
        <span className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
          <AdviceTypeBadge type={factor.advice_type} />
          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </span>
      </button>

      <div className={`drawer ${isOpen ? 'open' : ''} bg-slate-900 print-color-adjust`}>
        <div className="p-5 space-y-5 font-mono text-xs text-slate-200">
          {/* Evidence sources */}
          {sources.length > 0 ? (
            <div>
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-slate-400 mb-2">
                <GitBranch className="w-3 h-3" />
                JSON Path
              </div>
              <div className="space-y-1 break-words">
                {sources.map((src, i) => (
                  <div key={i} className="flex gap-2 text-[var(--color-cyan-code)]">
                    <span className="text-slate-500">→</span>
                    <span>{src}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-slate-500 italic">No evidence sources recorded.</div>
          )}

          {/* Threshold strip — Person A */}
          {hasThresholds && factor.feature === 'cibil_score' && (
            <div>
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-slate-400 mb-2">
                <Layers className="w-3 h-3" />
                Risk Tier Cutoffs
              </div>
              <div className="flex flex-wrap gap-2">
                <ThresholdChip label="P4 ≤" value={response.risk_tier.threshold_values.p4_max} />
                <ThresholdChip label="P3 ≥" value={response.risk_tier.threshold_values.p3_min} />
                <ThresholdChip label="P2 ≥" value={response.risk_tier.threshold_values.p2_min} />
                <ThresholdChip label="P1 ≥" value={response.risk_tier.threshold_values.p1_min} highlight />
              </div>
            </div>
          )}

          {/* Threshold strip — Person B financial_health */}
          {hasE5Thresholds && factor.feature === 'financial_health' && (
            <div>
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-slate-400 mb-2">
                <Layers className="w-3 h-3" />
                Readiness Thresholds
              </div>
              <div className="flex flex-wrap gap-2">
                <ThresholdChip
                  label="FH Floor"
                  value={response.readiness.metadata.e5_thresholds.financial_health_floor}
                />
                <ThresholdChip
                  label="Strong ≥"
                  value={response.readiness.metadata.e5_thresholds.strong_status_min}
                  highlight
                />
                <ThresholdChip
                  label="Ready ≥"
                  value={response.readiness.metadata.e5_thresholds.band_ready_min}
                />
              </div>
            </div>
          )}

          {/* Routing decision (if reroute happened) */}
          {response.routing_decision?.original_user_type !== response.routing_decision?.routed_to && (
            <div>
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-slate-400 mb-2">
                Routing
              </div>
              <div className="flex flex-wrap gap-2">
                <RoutingChip
                  label="From"
                  value={response.routing_decision.original_user_type}
                />
                <RoutingChip
                  label="To"
                  value={response.routing_decision.routed_to}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
