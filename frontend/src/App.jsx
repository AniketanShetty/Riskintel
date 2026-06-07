import { useEffect, useMemo, useState } from 'react'
import { Loader2, Inbox } from 'lucide-react'

import AppHeader from './components/AppHeader'
import OutcomeHero from './components/OutcomeHero'
import OverrideBanner from './components/OverrideBanner'
import StrengthsSection from './components/StrengthsSection'
import FocusAreasSection from './components/FocusAreasSection'
import DecisionTimeline from './components/DecisionTimeline'
import ArchitecturePage from './components/ArchitecturePage'
import LandingDashboard from './components/LandingDashboard'
import TraditionalAssessmentForm from './components/forms/TraditionalAssessmentForm'
import NTCAssessmentForm from './components/forms/NTCAssessmentForm'

function getVerdict(response) {
  if (!response) return ''
  if (response.user_type === 'person_a') return response.eligibility?.verdict || 'Pending'
  if (response.user_type === 'person_b') return response.readiness?.band || 'Pending'
  return 'Pending'
}

function hasPolicyOverride(response) {
  if (!response) return false
  if (response.user_type === 'person_a') return !!response.eligibility?.policy_override_applied
  if (response.user_type === 'person_b') return !!response.readiness?.metadata?.policy_override_applied
  return false
}

function splitFactors(response) {
  const all = response?.explanation?.contributing_factors || []
  return {
    strengths: all.filter((f) => f.is_strength),
    focus: all.filter((f) => !f.is_strength),
  }
}

export default function App() {
  const [currentPersona, setCurrentPersona] = useState(null)
  const [viewState, setViewState] = useState('landing') // landing, traditional_form, ntc_form, results
  const [isMentorMode, setIsMentorMode] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [showArchitecture, setShowArchitecture] = useState(false)

  useEffect(() => {
    if (isMentorMode) document.body.classList.add('mentor-mode')
    else document.body.classList.remove('mentor-mode')
  }, [isMentorMode])

  const handleSubmitAssessment = async (payload, endpointUrl) => {
    setIsLoading(true)
    try {
      const res = await fetch(endpointUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      
      if (!res.ok) throw new Error(`API Error: ${res.status}`)
      const liveAssessment = await res.json()
      
      const syntheticPersona = {
        id: `custom_${Date.now()}`,
        name: payload.full_name || "Applicant",
        user_type: payload.user_type,
        original_view: payload.user_type === 'person_a' ? 'traditional_form' : 'ntc_form',
        applicant: payload,
        ...liveAssessment
      }
      setCurrentPersona(syntheticPersona)
      setViewState('results')
    } catch (err) {
      console.error("API Error:", err)
      throw err 
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelectDemo = async (persona) => {
    setIsLoading(true)
    try {
      // Use unified endpoint so routing NTC works cleanly if needed
      const endpoint = 'http://localhost:8000/api/assess'
      
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(persona.applicant)
      })
      
      if (!res.ok) throw new Error(`API Error: ${res.status}`)
      const liveAssessment = await res.json()
      
      setCurrentPersona({
        ...persona,
        ...liveAssessment,
        original_view: persona.applicant.user_type === 'person_a' ? 'traditional_form' : 'ntc_form'
      })
      setViewState('results')
    } catch (err) {
      console.error("Failed to hit live API, falling back to mock data:", err)
      setCurrentPersona(persona)
      setViewState('results')
    } finally {
      setIsLoading(false)
    }
  }

  const handleClear = () => {
    setCurrentPersona(null)
    setViewState('landing')
  }

  const handleExport = () => {
    window.print()
  }

  const verdict = useMemo(() => getVerdict(currentPersona), [currentPersona])
  const override = useMemo(() => hasPolicyOverride(currentPersona), [currentPersona])
  const { strengths, focus } = useMemo(() => splitFactors(currentPersona), [currentPersona])

  return (
    <div className="min-h-screen transition-colors duration-300 relative">
      <AppHeader
        isMentorMode={isMentorMode}
        onToggleMentor={() => setIsMentorMode((v) => !v)}
        onExport={handleExport}
        showArchitecture={showArchitecture}
        setShowArchitecture={setShowArchitecture}
      />

      {showArchitecture && <ArchitecturePage onClose={() => setShowArchitecture(false)} />}

      <main className="max-w-5xl mx-auto mt-8 px-6 pb-24 space-y-8">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-8 h-8 text-slate-400 animate-spin" />
            <p className="text-slate-500 font-medium">Processing assessment…</p>
          </div>
        ) : viewState === 'landing' ? (
          <LandingDashboard 
            onSelectMode={setViewState} 
            onSelectPersona={handleSelectDemo}
            isMentorMode={isMentorMode}
          />
        ) : viewState === 'traditional_form' ? (
          <TraditionalAssessmentForm 
            onSubmit={handleSubmitAssessment} 
            isMentorMode={isMentorMode} 
            onCancel={handleClear} 
            initialData={currentPersona?.applicant}
          />
        ) : viewState === 'ntc_form' ? (
          <NTCAssessmentForm 
            onSubmit={handleSubmitAssessment} 
            isMentorMode={isMentorMode} 
            onCancel={handleClear} 
            initialData={currentPersona?.applicant}
          />
        ) : viewState === 'results' && currentPersona ? (
          <>
            <div className="flex justify-between items-end mb-4 print-color-adjust">
               <div>
                 <p className={`text-sm font-semibold uppercase tracking-wider ${isMentorMode ? 'text-slate-500' : 'text-slate-400'}`}>Assessment Reference ID</p>
                 <p className={`font-mono ${isMentorMode ? 'text-slate-400' : 'text-slate-600'}`}>ASMT-{currentPersona.id?.toUpperCase().replace('CUSTOM_','') || Date.now()}</p>
               </div>
               <button onClick={() => setViewState(currentPersona.original_view || (currentPersona.user_type === 'person_a' ? 'traditional_form' : 'ntc_form'))} className="text-sm font-medium text-blue-600 hover:text-blue-800 underline underline-offset-4">
                 Edit Assessment
               </button>
            </div>

            <DecisionTimeline 
              response={currentPersona} 
              isMentorMode={isMentorMode} 
            />

            <NTCRoutingBanner response={currentPersona} />

            {override && <OverrideBanner />}

            <OutcomeHero
              response={currentPersona}
              verdict={verdict}
              primaryReason={currentPersona.explanation?.primary_reason}
              userType={currentPersona.user_type}
              isMentorMode={isMentorMode}
            />

            <div className="grid md:grid-cols-2 gap-8">
              <StrengthsSection
                factors={strengths}
                isMentorMode={isMentorMode}
                response={currentPersona}
              />
              <FocusAreasSection
                factors={focus}
                isMentorMode={isMentorMode}
                response={currentPersona}
              />
            </div>
          </>
        ) : null}
      </main>
    </div>
  )
}

function NTCRoutingBanner({ response }) {
  if (!response || response.routing_decision?.routed_to !== 'person_b') return null;
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex gap-4 items-start print-color-adjust">
      <div className="flex-shrink-0 mt-0.5">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-600"><circle cx="6" cy="19" r="3"></circle><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"></path><circle cx="18" cy="5" r="3"></circle></svg>
      </div>
      <div>
        <h4 className="font-semibold text-blue-900 text-sm">NTC Route Activated</h4>
        <p className="text-sm text-blue-800 mt-0.5">
          CIBIL not available. Alternative Data Assessment Used.
        </p>
      </div>
    </div>
  )
}
