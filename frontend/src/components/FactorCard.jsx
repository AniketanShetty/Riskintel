import { Check, ArrowRight, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import EvidenceDrawer from './EvidenceDrawer'

function resolveValue(feature, response) {
  // Hide literal "Unknown" — resolve from parent data per project rules
  const applicant = response.applicant || {}

  // Person A: input echoes
  if (response.user_type === 'person_a') {
    if (feature === 'cibil_score' && response.risk_tier?.score_used != null) {
      return response.risk_tier.score_used
    }
    if (['loan_amount', 'annual_income', 'loan_term'].includes(feature)) {
      if (applicant[feature] != null) return applicant[feature]
    }
  }

  // Person B: readiness component score
  if (response.user_type === 'person_b') {
    const comp = response.readiness?.components?.[feature]
    if (comp && typeof comp.score === 'number') return comp.score
  }

  return null
}

function formatFeature(feature) {
  return feature
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

function formatValue(feature, value) {
  if (typeof value === 'number' && feature.toLowerCase().includes('amount')) {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value)
  }
  if (typeof value === 'number' && feature === 'cibil_score') {
    return String(value)
  }
  if (typeof value === 'number') return String(value)
  return null
}

export default function FactorCard({ factor, isStrength, isMentorMode, response, defaultOpen = false }) {
  const [drawerOpen, setDrawerOpen] = useState(defaultOpen && isMentorMode)

  // Strength styling
  const accentText = isStrength ? 'text-[var(--color-sage)]' : 'text-[var(--color-ochre)]'
  const accentBg = isStrength ? 'bg-[var(--color-sage-light)]' : 'bg-[var(--color-ochre-light)]'
  const accentBorder = isStrength ? 'border-[var(--color-sage)]/30' : 'border-[var(--color-ochre)]/30'
  const leftBorder = isStrength ? '' : 'border-l-4 border-l-[var(--color-ochre)]'
  const Icon = isStrength ? Check : ArrowRight

  const resolved = resolveValue(factor.feature, response)
  const formatted = resolved != null ? formatValue(factor.feature, resolved) : null

  return (
    <article
      className={`bg-white rounded-2xl shadow-sm border ${accentBorder} overflow-hidden transition-shadow duration-150 hover:shadow-md print-color-adjust`}
    >
      <div className={`p-6 flex gap-4 ${leftBorder}`}>
        <div
          className={`flex-shrink-0 w-9 h-9 rounded-full ${accentBg} flex items-center justify-center ${accentText}`}
        >
          <Icon className="w-5 h-5" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 flex-wrap">
            <h4 className="font-semibold text-[var(--color-primary)] text-base">
              {formatFeature(factor.feature)}
            </h4>
            {formatted != null && (
              <span className={`text-sm font-mono font-semibold ${accentText}`}>
                {formatted}
              </span>
            )}
          </div>

          <p className="text-slate-600 mt-2 leading-relaxed text-[15px]">
            {factor.reason}
          </p>

          {factor.improvement_advice && (
            <div className="mt-4 p-3.5 rounded-lg bg-slate-50 border border-slate-100">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1">
                {isStrength ? 'Keep doing this' : 'Action plan'}
              </p>
              <p className="text-sm text-slate-700 leading-relaxed italic">
                “{factor.improvement_advice}”
              </p>
            </div>
          )}
        </div>
      </div>

      {isMentorMode && (
        <EvidenceDrawer
          factor={factor}
          response={response}
          isOpen={drawerOpen}
          onToggle={() => setDrawerOpen(!drawerOpen)}
        />
      )}
    </article>
  )
}
