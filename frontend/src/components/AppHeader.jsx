import { Shield } from 'lucide-react'
import MentorToggle from './MentorToggle'
import ExportButton from './ExportButton'

export default function AppHeader({ isMentorMode, onToggleMentor, onExport }) {
  return (
    <header className="app-header sticky top-0 z-20 bg-white shadow-sm border-b border-slate-200 px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-3 no-print transition-colors duration-300">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-9 h-9 rounded-lg bg-[var(--color-primary)] flex items-center justify-center flex-shrink-0">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <div className="min-w-0">
          <h1 className="text-lg font-semibold tracking-tight text-[var(--color-primary)] transition-colors duration-300 truncate">
            RiskIntel
          </h1>
          <p className="hidden sm:block text-[11px] uppercase tracking-wider text-slate-500 font-medium truncate">
            Borrower Coaching Report
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-4 flex-wrap">
        <MentorToggle isMentorMode={isMentorMode} onToggle={onToggleMentor} />
        <ExportButton onClick={onExport} />
      </div>
    </header>
  )
}
