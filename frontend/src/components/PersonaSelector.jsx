import { User, X } from 'lucide-react'

export default function PersonaSelector({ personas, currentId, onSelect, onClear }) {
  return (
    <section className="no-print max-w-5xl mx-auto mt-8 px-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-slate-500" />
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Demo Personas
            </h2>
          </div>
          {currentId && (
            <button
              type="button"
              onClick={onClear}
              className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800 transition-colors duration-150"
            >
              <X className="w-3 h-3" />
              Clear
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {personas.map((p) => {
            const isActive = currentId === p.id
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => onSelect(p)}
                className={`text-sm px-4 py-2.5 rounded-lg border transition-colors duration-150 text-left ${
                  isActive
                    ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)] shadow-sm'
                    : 'bg-white text-slate-700 border-slate-200 hover:border-slate-400 hover:bg-slate-50'
                }`}
                style={{ minHeight: 44 }}
              >
                <span className="font-medium">{p.name}</span>
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}
