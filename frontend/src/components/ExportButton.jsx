import { FileDown } from 'lucide-react'

export default function ExportButton({ onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 text-sm font-medium text-slate-700"
    >
      <FileDown className="w-4 h-4" />
      <span className="hidden sm:inline">Print Report</span>
    </button>
  )
}
