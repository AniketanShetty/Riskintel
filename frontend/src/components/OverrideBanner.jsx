import { AlertTriangle } from 'lucide-react'

export default function OverrideBanner() {
  return (
    <div
      role="alert"
      className="animate-slide-down rounded-xl border-l-4 border-[var(--color-amber-alert)] bg-amber-50 p-5 shadow-sm flex gap-4 items-start print-color-adjust"
    >
      <div className="flex-shrink-0 mt-0.5">
        <AlertTriangle className="w-6 h-6 text-[var(--color-amber-alert)]" />
      </div>
      <div>
        <h3 className="font-bold text-amber-900 text-base">
          Policy Override Applied
        </h3>
        <p className="text-sm text-amber-800 mt-1 leading-relaxed">
          Final decision was affected by a governance rule. The machine learning
          prediction was not the deciding factor in this outcome.
        </p>
      </div>
    </div>
  )
}
