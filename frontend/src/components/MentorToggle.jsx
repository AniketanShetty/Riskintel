import { Eye, EyeOff } from 'lucide-react'

export default function MentorToggle({ isMentorMode, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={isMentorMode}
      className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 transition-colors duration-150 text-sm font-medium text-slate-700"
    >
      <span className="relative flex items-center justify-center w-4 h-4">
        {isMentorMode
          ? <Eye className="w-4 h-4 text-[var(--color-amber-alert)]" />
          : <EyeOff className="w-4 h-4 text-slate-500" />}
        {isMentorMode && (
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-[var(--color-amber-alert)] animate-fade-in" />
        )}
      </span>
      <span>Mentor Mode</span>
      <span
        className={`ml-1 text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded ${
          isMentorMode
            ? 'bg-[var(--color-slate-ash)] text-[var(--color-cyan-code)]'
            : 'bg-slate-100 text-slate-500'
        }`}
      >
        {isMentorMode ? 'On' : 'Off'}
      </span>
    </button>
  )
}
