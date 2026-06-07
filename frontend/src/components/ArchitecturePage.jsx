import { ArrowDown, Server, Database, ShieldAlert, Cpu, Route, Users, Layout, X } from 'lucide-react'

export default function ArchitecturePage({ onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-900/60 backdrop-blur-sm p-4 sm:p-6 print-color-adjust">
      <div className="relative w-full max-w-5xl bg-white rounded-3xl shadow-2xl my-4 sm:my-8 overflow-hidden animate-fade-in border border-slate-200">
        
        <div className="sticky top-0 z-20 bg-white/90 backdrop-blur-md border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl sm:text-2xl font-bold text-slate-800">How RiskIntel Works</h2>
          <button 
            onClick={onClose}
            className="p-2 rounded-full hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 sm:p-10 space-y-12">
          <div className="text-center space-y-4">
            <p className="text-slate-600 max-w-2xl mx-auto text-lg">
              RiskIntel is an explainable AI underwriting system. It separates the statistical math (ML) from 
              the deterministic policy (Governance) to ensure every borrower receives legally actionable coaching.
            </p>
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 text-center max-w-3xl mx-auto">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-2">The Problem We Solve</h3>
            <p className="text-slate-600 text-sm sm:text-base">
              Millions of borrowers lack formal credit history. Traditional scoring automatically rejects them. 
              RiskIntel bridges this gap by evaluating alternative infrastructure and financial readiness signals.
            </p>
          </div>

          <div className="relative">
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-200 -translate-x-1/2 hidden md:block" />
            
            <div className="space-y-8 relative">
              
              {/* Step 1: Input */}
              <div className="flex flex-col md:flex-row items-center justify-center gap-6">
                <div className="w-full md:w-5/12 flex justify-end">
                  <div className="bg-slate-50 border border-slate-200 p-5 rounded-2xl shadow-sm w-full md:w-auto md:text-right">
                    <div className="flex items-center gap-2 md:justify-end mb-2 text-indigo-600">
                      <Database className="w-5 h-5" />
                      <h3 className="font-semibold">1. Input Payload</h3>
                    </div>
                    <p className="text-sm text-slate-600">Borrower profile (Income, Age, CIBIL, Assets) is submitted via the API.</p>
                  </div>
                </div>
                <div className="hidden md:flex w-12 h-12 rounded-full bg-indigo-100 border-4 border-white items-center justify-center z-10 shrink-0">
                  <span className="text-indigo-600 font-bold">1</span>
                </div>
                <div className="w-full md:w-5/12" />
              </div>

              <div className="flex justify-center md:hidden text-slate-300"><ArrowDown /></div>

              {/* Step 2: Routing */}
              <div className="flex flex-col md:flex-row-reverse items-center justify-center gap-6">
                <div className="w-full md:w-5/12 flex justify-start">
                  <div className="bg-slate-50 border border-slate-200 p-5 rounded-2xl shadow-sm w-full md:w-auto">
                    <div className="flex items-center gap-2 mb-2 text-blue-600">
                      <Route className="w-5 h-5" />
                      <h3 className="font-semibold">2. Routing Engine</h3>
                    </div>
                    <p className="text-sm text-slate-600">Detects if the applicant has a CIBIL score. If CIBIL = 0, routes to NTC (New-To-Credit) pipeline.</p>
                  </div>
                </div>
                <div className="hidden md:flex w-12 h-12 rounded-full bg-blue-100 border-4 border-white items-center justify-center z-10 shrink-0">
                  <span className="text-blue-600 font-bold">2</span>
                </div>
                <div className="w-full md:w-5/12" />
              </div>

              <div className="flex justify-center md:hidden text-slate-300"><ArrowDown /></div>

              {/* Step 3: Dual Engines */}
              <div className="flex flex-col md:flex-row items-center justify-center gap-6">
                <div className="w-full md:w-5/12 flex justify-end">
                  <div className="bg-slate-800 text-slate-200 border border-slate-700 p-5 rounded-2xl shadow-sm w-full">
                    <div className="flex items-center gap-2 md:justify-end mb-2 text-emerald-400">
                      <Cpu className="w-5 h-5" />
                      <h3 className="font-semibold">3A. Eligibility Engine</h3>
                    </div>
                    <p className="text-sm text-slate-400 mb-3 md:text-right">For traditional borrowers (Person A).</p>
                    <ul className="text-xs space-y-1 md:text-right text-slate-300">
                      <li>• Uses Random Forest ML</li>
                      <li>• Extracts local SHAP contributions</li>
                    </ul>
                  </div>
                </div>
                <div className="hidden md:flex w-12 h-12 rounded-full bg-emerald-100 border-4 border-white items-center justify-center z-10 shrink-0">
                  <span className="text-emerald-600 font-bold">3</span>
                </div>
                <div className="w-full md:w-5/12 flex justify-start">
                  <div className="bg-slate-800 text-slate-200 border border-slate-700 p-5 rounded-2xl shadow-sm w-full">
                    <div className="flex items-center gap-2 mb-2 text-teal-400">
                      <Server className="w-5 h-5" />
                      <h3 className="font-semibold">3B. Readiness Engine</h3>
                    </div>
                    <p className="text-sm text-slate-400 mb-3">For NTC borrowers (Person B).</p>
                    <ul className="text-xs space-y-1 text-slate-300">
                      <li>• Deterministic proxy math</li>
                      <li>• Analyzes cash flow & infrastructure</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="flex justify-center md:hidden text-slate-300"><ArrowDown /></div>

              {/* Step 4: Governance */}
              <div className="flex flex-col md:flex-row-reverse items-center justify-center gap-6">
                <div className="w-full md:w-5/12 flex justify-start">
                  <div className="bg-amber-50 border border-amber-200 p-5 rounded-2xl shadow-sm w-full md:w-auto">
                    <div className="flex items-center gap-2 mb-2 text-amber-600">
                      <ShieldAlert className="w-5 h-5" />
                      <h3 className="font-semibold">4. Governance Layer</h3>
                    </div>
                    <p className="text-sm text-amber-800">
                      Enforces absolute policy thresholds. If the ML approves a high-risk tier (P4) or the NTC score hits a financial health floor, Governance explicitly vetoes the decision.
                    </p>
                  </div>
                </div>
                <div className="hidden md:flex w-12 h-12 rounded-full bg-amber-100 border-4 border-white items-center justify-center z-10 shrink-0">
                  <span className="text-amber-600 font-bold">4</span>
                </div>
                <div className="w-full md:w-5/12" />
              </div>

              <div className="flex justify-center md:hidden text-slate-300"><ArrowDown /></div>

              {/* Step 5: Explainability */}
              <div className="flex flex-col md:flex-row items-center justify-center gap-6">
                <div className="w-full md:w-5/12 flex justify-end">
                  <div className="bg-slate-50 border border-slate-200 p-5 rounded-2xl shadow-sm w-full md:w-auto md:text-right">
                    <div className="flex items-center gap-2 md:justify-end mb-2 text-purple-600">
                      <Users className="w-5 h-5" />
                      <h3 className="font-semibold">5. Recommendation Engine</h3>
                    </div>
                    <p className="text-sm text-slate-600">Translates negative mathematical factors into plain English. Strips out unchangeable traits (Age, Education) to ensure advice is strictly actionable.</p>
                  </div>
                </div>
                <div className="hidden md:flex w-12 h-12 rounded-full bg-purple-100 border-4 border-white items-center justify-center z-10 shrink-0">
                  <span className="text-purple-600 font-bold">5</span>
                </div>
                <div className="w-full md:w-5/12" />
              </div>

              <div className="flex justify-center md:hidden text-slate-300"><ArrowDown /></div>

              {/* Step 6: Frontend Modes */}
              <div className="flex flex-col md:flex-row-reverse items-center justify-center gap-6">
                <div className="w-full md:w-5/12 flex justify-start">
                  <div className="bg-slate-50 border border-slate-200 p-5 rounded-2xl shadow-sm w-full md:w-auto">
                    <div className="flex items-center gap-2 mb-2 text-rose-600">
                      <Layout className="w-5 h-5" />
                      <h3 className="font-semibold">6. Borrower vs Mentor Mode</h3>
                    </div>
                    <p className="text-sm text-slate-600 mb-2">The frontend natively hides correlation IDs and rule boundaries from the borrower view to prevent confusion.</p>
                    <p className="text-sm text-slate-600">The <strong>Mentor Toggle</strong> reveals the underlying JSON paths and thresholds for compliance X-Ray.</p>
                  </div>
                </div>
                <div className="hidden md:flex w-12 h-12 rounded-full bg-rose-100 border-4 border-white items-center justify-center z-10 shrink-0">
                  <span className="text-rose-600 font-bold">6</span>
                </div>
                <div className="w-full md:w-5/12" />
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
