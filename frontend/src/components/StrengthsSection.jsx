import FactorCard from './FactorCard'

export default function StrengthsSection({ factors, isMentorMode, response }) {
  if (!factors || factors.length === 0) return null

  return (
    <section className="space-y-4">
      <header className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-[var(--color-sage)]" />
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Profile Strengths
        </h3>
        <span className="text-[11px] text-slate-400 ml-1">
          {factors.length} {factors.length === 1 ? 'area' : 'areas'}
        </span>
      </header>
      <div className="space-y-4">
        {factors.map((f, i) => (
          <FactorCard
            key={`${f.feature}-${i}`}
            factor={f}
            isStrength
            isMentorMode={isMentorMode}
            response={response}
            defaultOpen={i === 0}
          />
        ))}
      </div>
    </section>
  )
}
