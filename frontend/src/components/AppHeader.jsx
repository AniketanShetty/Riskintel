import { Shield } from 'lucide-react'
import MentorToggle from './MentorToggle'
import ExportButton from './ExportButton'

export default function AppHeader({ isMentorMode, onToggleMentor, onExport }) {
  return (
    <header className="app-header sticky top-0 z-20 bg-white shadow-sm border-b border-slate-200 px-6 py-4 flex items-center justify-between no-print transition-colors duration-300">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-[var(--color-primary)] flex items-center justify-center">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-[var(--color-primary)] transition-colors duration-300">
            RiskIntel
          </h1>
          <p className="text-[11px] uppercase tracking-wider text-slate-500 font-medium">
            Borrower Coaching Report
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <MentorToggle isMentorMode={isMentorMode} onToggle={onToggleMentor} />
        <ExportButton onClick={onExport} />
      </div>
    </header>
  )
}
