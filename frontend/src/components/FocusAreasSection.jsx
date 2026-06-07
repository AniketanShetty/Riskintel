import { Target } from 'lucide-react'
import FactorCard from './FactorCard'

export default function FocusAreasSection({ factors, isMentorMode, response }) {
  if (!factors || factors.length === 0) return null

  return (
    <section className="space-y-4">
      <header className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-[var(--color-ochre)]" />
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {isMentorMode ? 'Focus Area' : 'Improvement Horizon'}
        </h3>
        <span className="text-[11px] text-slate-400 ml-1">
          {factors.length === 1 ? 'One primary' : `${factors.length} areas`}
        </span>
      </header>
      <div className="space-y-4">
        {factors.map((f, i) => (
          <FactorCard
            key={`${f.feature}-${i}`}
            factor={f}
            isStrength={false}
            isMentorMode={isMentorMode}
            response={response}
            defaultOpen={factors.length === 1 && i === 0}
          />
        ))}
      </div>
    </section>
  )
}
