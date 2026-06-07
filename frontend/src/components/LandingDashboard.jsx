import PersonaSelector from './PersonaSelector';
import mockPersonas from '../data/mockPersonas.json';
import { UserCircle, Sprout, Lightbulb } from 'lucide-react';

export default function LandingDashboard({ onSelectMode, onSelectPersona, isMentorMode }) {
  return (
    <div className={`rounded-3xl p-8 md:p-12 border shadow-sm animate-fade-in ${isMentorMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'}`}>
      
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto space-y-4 mb-12">
        <h2 className={`text-4xl md:text-5xl font-bold tracking-tight ${isMentorMode ? 'text-slate-100' : 'text-slate-900'}`}>
          RiskIntel
        </h2>
        <p className={`text-lg md:text-xl ${isMentorMode ? 'text-slate-400' : 'text-slate-600'}`}>
          Explainable Credit Intelligence for Traditional and New-To-Credit Borrowers
        </p>
      </div>

      {/* Primary Action Paths */}
      <div className="grid md:grid-cols-2 gap-6 mb-16">
        <button
          onClick={() => onSelectMode('traditional_form')}
          className={`flex flex-col items-start text-left p-8 rounded-2xl border transition-all duration-200 group hover:-translate-y-1 hover:shadow-md ${
            isMentorMode 
              ? 'bg-slate-900/50 border-slate-700/50 hover:border-blue-500/50 hover:bg-slate-800' 
              : 'bg-slate-50 border-slate-100 hover:border-blue-200 hover:bg-blue-50/50'
          }`}
        >
          <div className={`p-3 rounded-xl mb-4 ${isMentorMode ? 'bg-blue-900/50 text-blue-400' : 'bg-blue-100 text-blue-600'}`}>
            <UserCircle size={28} />
          </div>
          <h3 className={`text-xl font-semibold mb-2 ${isMentorMode ? 'text-slate-200' : 'text-slate-800'}`}>
            Standard Credit Assessment
          </h3>
          <p className={`text-sm ${isMentorMode ? 'text-slate-400' : 'text-slate-600'}`}>
            For established borrowers with existing credit histories. Evaluates applications using robust, explainable ML models based on structured financial data.
          </p>
        </button>

        <button
          onClick={() => onSelectMode('ntc_form')}
          className={`flex flex-col items-start text-left p-8 rounded-2xl border transition-all duration-200 group hover:-translate-y-1 hover:shadow-md ${
            isMentorMode 
              ? 'bg-slate-900/50 border-slate-700/50 hover:border-emerald-500/50 hover:bg-slate-800' 
              : 'bg-slate-50 border-slate-100 hover:border-emerald-200 hover:bg-emerald-50/50'
          }`}
        >
          <div className={`p-3 rounded-xl mb-4 ${isMentorMode ? 'bg-emerald-900/50 text-emerald-400' : 'bg-emerald-100 text-emerald-600'}`}>
            <Sprout size={28} />
          </div>
          <h3 className={`text-xl font-semibold mb-2 ${isMentorMode ? 'text-slate-200' : 'text-slate-800'}`}>
            Alternative Data Assessment
          </h3>
          <p className={`text-sm ${isMentorMode ? 'text-slate-400' : 'text-slate-600'}`}>
            A modern pathway for self-employed and unbanked individuals. Generates readiness scores using infrastructural and livelihood proxies.
          </p>
        </button>
      </div>

      {/* How RiskIntel Works */}
      <div className={`p-6 rounded-2xl mb-16 border flex gap-4 items-start ${isMentorMode ? 'bg-indigo-900/20 border-indigo-500/20' : 'bg-indigo-50/50 border-indigo-100'}`}>
        <div className={`mt-1 ${isMentorMode ? 'text-indigo-400' : 'text-indigo-500'}`}>
          <Lightbulb size={24} />
        </div>
        <div>
          <h4 className={`font-semibold mb-1 ${isMentorMode ? 'text-indigo-300' : 'text-indigo-900'}`}>How RiskIntel Works</h4>
          <p className={`text-sm leading-relaxed ${isMentorMode ? 'text-indigo-200/80' : 'text-indigo-800/80'}`}>
            RiskIntel uses fair, explainable intelligence to look beyond standard scores. Whether through traditional underwriting or alternative readiness metrics, every applicant receives a transparent path toward financial inclusion.
          </p>
        </div>
      </div>

      {/* Demo Scenarios Section */}
      <div className="pt-8 border-t border-slate-200/20">
        <div className="text-center mb-6">
          <p className={`text-sm font-medium uppercase tracking-wider ${isMentorMode ? 'text-slate-500' : 'text-slate-400'}`}>
            Or Choose a Pre-configured Demo Scenario
          </p>
        </div>
        <div className="-mx-4">
          <PersonaSelector
            personas={mockPersonas}
            currentId={null}
            onSelect={onSelectPersona}
            onClear={() => {}}
          />
        </div>
      </div>

    </div>
  );
}
