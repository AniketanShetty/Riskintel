import { CheckCircle2, XCircle, AlertCircle, Sparkles } from 'lucide-react'
import ScoreVisualizer from './ScoreVisualizer'

// Borrower Language Rules Translator
function translateBorrowerLanguage(verdict, isMentorMode) {
  if (isMentorMode) return verdict; // Mentor sees raw engine strings

  const map = {
    'Unlikely': 'Additional Preparation Recommended',
    'Not Ready': 'Eligibility Requirements Not Yet Met',
    'Borderline': 'Opportunity for Improvement',
    'Needs Improvement': 'Opportunity for Improvement',
    'Moderately Ready': 'Developing Profile',
    'Likely': 'Approved',
    'Highly Likely': 'Approved',
    'Ready': 'Approved'
  };

  return map[verdict] || verdict;
}

function toneFor(verdict, userType) {
  if (userType === 'person_a') {
    if (verdict === 'Highly Likely' || verdict === 'Likely') return 'positive'
    if (verdict === 'Borderline') return 'neutral'
    return 'negative'
  }
  if (verdict === 'Ready') return 'positive'
  if (verdict === 'Moderately Ready' || verdict === 'Needs Improvement') return 'neutral'
  return 'negative'
}

function VerdictIcon({ tone }) {
  if (tone === 'positive') return <CheckCircle2 className="w-12 h-12 text-[var(--color-sage)]" />
  if (tone === 'neutral') return <AlertCircle className="w-12 h-12 text-[var(--color-ochre)]" />
  return <XCircle className="w-12 h-12 text-slate-500" />
}

function generateDecisionSummary(response, tone, isMentorMode) {
  if (!response) return '';
  const isPersonA = response.user_type === 'person_a';
  const isOverride = isPersonA 
    ? !!response.eligibility?.policy_override_applied 
    : !!response.readiness?.metadata?.policy_override_applied;

  if (isPersonA) {
    if (tone === 'positive') return "Approved because of a strong traditional credit profile.";
    if (isOverride) return isMentorMode ? "Rejected because banking policy requirements were not met despite the initial assessment." : "Currently Not Eligible due to banking policy requirements.";
    return isMentorMode ? "Rejected because traditional credit requirements were not met." : "Currently Not Eligible based on traditional credit requirements.";
  } else {
    if (tone === 'positive') return "Approved through alternative-data assessment despite no formal credit history.";
    const isMisaligned = response.readiness?.components?.business_viability?.factors?.purpose_alignment === 'Misaligned';
    if (isMisaligned) return isMentorMode ? "Rejected because loan purpose does not align with primary business operations." : "Currently Not Eligible. We recommend aligning loan purpose with primary business operations.";
    return isMentorMode ? "Rejected because financial or operational readiness remains below required thresholds." : "Currently Not Eligible. Additional preparation in financial or operational readiness is recommended.";
  }
}

export default function OutcomeHero({ response, verdict, primaryReason, userType, isMentorMode }) {
  const tone = toneFor(verdict, userType)
  const labelPrefix = isMentorMode ? (userType === 'person_a' ? 'Engine Decision' : 'Engine Readiness') : 'Assessment Outcome'
  const decisionSummary = generateDecisionSummary(response, tone, isMentorMode)
  
  const displayVerdict = translateBorrowerLanguage(verdict, isMentorMode)

  return (
    <section
      className={`rounded-3xl border p-8 md:p-10 shadow-sm ${
        isMentorMode
          ? 'bg-slate-800 border-slate-700 text-slate-100 print:bg-white print:border-slate-200 print:text-[var(--color-primary)]'
          : 'bg-white border-slate-200 text-[var(--color-primary)]'
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
        <div className="flex flex-col sm:flex-row sm:items-start gap-4 sm:gap-6 flex-1">
          <div className="flex-shrink-0 self-start sm:self-auto mt-1">
            <VerdictIcon tone={tone} />
          </div>
          <div className="flex-1 min-w-0">
            <p
              className={`text-xs font-semibold uppercase tracking-wider mb-2 ${
                isMentorMode ? 'text-[var(--color-cyan-code)]' : 'text-slate-500'
              }`}
            >
              {labelPrefix}
            </p>
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight leading-tight">
              {displayVerdict}
            </h2>
            
            {/* Show raw reason in Mentor Mode, else hide the raw ML string to prevent confusion */}
            {isMentorMode && primaryReason && (
              <p className="mt-4 text-lg md:text-xl leading-relaxed text-slate-300">
                {primaryReason}
              </p>
            )}
            
            {decisionSummary && (
              <p
                className={`mt-3 text-base md:text-lg font-medium ${
                  isMentorMode ? 'text-slate-400' : 'text-slate-600'
                }`}
              >
                {decisionSummary}
              </p>
            )}

            {tone === 'positive' && !isMentorMode && (
              <div className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-[var(--color-sage)] bg-[var(--color-sage-light)] px-3 py-1.5 rounded-full">
                <Sparkles className="w-4 h-4" />
                Profile meets the criteria
              </div>
            )}
          </div>
        </div>

        <div className="hidden md:block flex-shrink-0">
          <ScoreVisualizer response={response} isMentorMode={isMentorMode} />
        </div>
      </div>
    </section>
  )
}
