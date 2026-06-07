import { useEffect, useMemo, useState } from 'react'
import { Loader2, Inbox } from 'lucide-react'

import AppHeader from './components/AppHeader'
import PersonaSelector from './components/PersonaSelector'
import OutcomeHero from './components/OutcomeHero'
import OverrideBanner from './components/OverrideBanner'
import StrengthsSection from './components/StrengthsSection'
import FocusAreasSection from './components/FocusAreasSection'

import mockPersonas from './data/mockPersonas.json'

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
  const [isMentorMode, setIsMentorMode] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (isMentorMode) document.body.classList.add('mentor-mode')
    else document.body.classList.remove('mentor-mode')
  }, [isMentorMode])

  const handleSelect = (persona) => {
    setIsLoading(true)
    setTimeout(() => {
      setCurrentPersona(persona)
      setIsLoading(false)
    }, 600)
  }

  const handleClear = () => setCurrentPersona(null)

  const handleExport = () => {
    window.print()
  }

  const verdict = useMemo(() => getVerdict(currentPersona), [currentPersona])
  const override = useMemo(() => hasPolicyOverride(currentPersona), [currentPersona])
  const { strengths, focus } = useMemo(() => splitFactors(currentPersona), [currentPersona])

  return (
    <div className="min-h-screen transition-colors duration-300">
      <AppHeader
        isMentorMode={isMentorMode}
        onToggleMentor={() => setIsMentorMode((v) => !v)}
        onExport={handleExport}
      />

      <PersonaSelector
        personas={mockPersonas}
        currentId={currentPersona?.id}
        onSelect={handleSelect}
        onClear={handleClear}
      />

      <main className="max-w-5xl mx-auto mt-8 px-6 pb-24 space-y-8">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-8 h-8 text-slate-400 animate-spin" />
            <p className="text-slate-500 font-medium">Loading assessment…</p>
          </div>
        ) : !currentPersona ? (
          <EmptyState isMentorMode={isMentorMode} />
        ) : (
          <>
            {override && <OverrideBanner />}

            <OutcomeHero
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
        )}
      </main>
    </div>
  )
}

function EmptyState({ isMentorMode }) {
  return (
    <div
      className={`rounded-3xl border border-dashed p-16 text-center ${
        isMentorMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-300'
      }`}
    >
      <Inbox
        className={`w-12 h-12 mx-auto mb-4 ${
          isMentorMode ? 'text-slate-600' : 'text-slate-300'
        }`}
      />
      <h2
        className={`text-xl font-semibold mb-2 ${
          isMentorMode ? 'text-slate-200' : 'text-slate-700'
        }`}
      >
        Select a demo persona
      </h2>
      <p
        className={`text-sm ${isMentorMode ? 'text-slate-400' : 'text-slate-500'}`}
      >
        Choose one of the personas above to view the borrower coaching report.
      </p>
    </div>
  )
}
