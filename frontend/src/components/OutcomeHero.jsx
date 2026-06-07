import { CheckCircle2, XCircle, AlertCircle, Sparkles } from 'lucide-react'

function toneFor(verdict, userType) {
  // Person A verdicts: Highly Likely | Likely | Borderline | Unlikely
  // Person B bands:   Ready | Moderately Ready | Needs Improvement | Not Ready
  if (userType === 'person_a') {
    if (verdict === 'Highly Likely' || verdict === 'Likely') return 'positive'
    if (verdict === 'Borderline') return 'neutral'
    return 'negative'
  }
  if (verdict === 'Ready') return 'positive'
  if (verdict === 'Moderately Ready' || verdict === 'Needs Improvement') return 'neutral'
  return 'negative'
}

function VerdictIcon({ tone }) {
  if (tone === 'positive') return <CheckCircle2 className="w-12 h-12 text-[var(--color-sage)]" />
  if (tone === 'neutral') return <AlertCircle className="w-12 h-12 text-[var(--color-ochre)]" />
  return <XCircle className="w-12 h-12 text-slate-500" />
}

export default function OutcomeHero({ verdict, primaryReason, userType, isMentorMode }) {
  const tone = toneFor(verdict, userType)
  const labelPrefix = userType === 'person_a' ? 'Decision' : 'Readiness'

  return (
    <section
      className={`rounded-3xl border p-8 md:p-10 shadow-sm print-color-adjust ${
        isMentorMode
          ? 'bg-slate-800 border-slate-700 text-slate-100'
          : 'bg-white border-slate-200 text-[var(--color-primary)]'
      }`}
    >
      <div className="flex items-start gap-6">
        <div className="flex-shrink-0">
          <VerdictIcon tone={tone} />
        </div>
        <div className="flex-1 min-w-0">
          <p
            className={`text-xs font-semibold uppercase tracking-wider mb-2 ${
              isMentorMode ? 'text-[var(--color-cyan-code)]' : 'text-slate-500'
            }`}
          >
            {labelPrefix}
          </p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight leading-tight">
            {verdict}
          </h2>
          <p
            className={`mt-4 text-lg md:text-xl leading-relaxed ${
              isMentorMode ? 'text-slate-300' : 'text-slate-600'
            }`}
          >
            {primaryReason}
          </p>
        </div>
      </div>

      {tone === 'positive' && !isMentorMode && (
        <div className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-[var(--color-sage)] bg-[var(--color-sage-light)] px-3 py-1.5 rounded-full">
          <Sparkles className="w-4 h-4" />
          Profile meets the criteria
        </div>
      )}
    </section>
  )
}
