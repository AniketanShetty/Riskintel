import { CheckCircle2, AlertCircle, ArrowRight, Copy } from 'lucide-react'

export default function DecisionTimeline({ response, isMentorMode }) {
  if (!isMentorMode || !response) return null;

  const steps = [];
  
  // 1. Request Received
  steps.push({
    title: "Request Received",
    detail: (
      <div className="flex items-center gap-1">
        <span>ID: {response.correlation_id?.substring(0,8) || 'N/A'}...</span>
        {response.correlation_id && (
          <button 
            onClick={() => navigator.clipboard.writeText(response.correlation_id)}
            className="p-0.5 hover:bg-slate-700 rounded text-slate-400 hover:text-slate-200 transition-colors"
            title="Copy Correlation ID"
          >
            <Copy className="w-3 h-3" />
          </button>
        )}
      </div>
    ),
    status: "success"
  });

  // 2. Routing Decision
  if (response.routing_decision) {
     steps.push({
        title: "Routing Engine",
        detail: `Routed to ${response.routing_decision.routed_to === 'person_a' ? 'Eligibility Engine' : 'Readiness Engine'}`,
        status: "success"
     });
  }

  // 3. Engine Execution
  if (response.user_type === 'person_a') {
     steps.push({
        title: "Eligibility Engine",
        detail: `Probability: ${((response.eligibility?.probability || 0) * 100).toFixed(1)}%`,
        status: "success"
     });
     if (response.risk_tier) {
         steps.push({
             title: "Governance Layer",
             detail: `Tier: ${response.risk_tier.tier} (${response.risk_tier.label})`,
             status: "success"
         });
     }
  } else if (response.user_type === 'person_b') {
     steps.push({
        title: "Readiness Engine",
        detail: `Score: ${response.readiness?.score || 0}/100`,
        status: "success"
     });
  }

  // 4. Policy Override
  const override = response.user_type === 'person_a' 
      ? response.eligibility?.policy_override_applied 
      : response.readiness?.metadata?.policy_override_applied;
  
  if (override) {
     steps.push({
        title: "Policy Override",
        detail: "Floor breach triggered",
        status: "warning"
     });
  }

  // 5. Recommendations
  steps.push({
     title: "Recommendation Engine",
     detail: `${response.explanation?.contributing_factors?.length || 0} factors generated`,
     status: "success"
  });

  // 6. Final Decision
  steps.push({
     title: "Final Decision",
     detail: response.explanation?.decision_verdict || "Pending",
     status: override ? "warning" : "success"
  });

  return (
    <div className="bg-slate-800 rounded-2xl p-6 mb-8 border border-slate-700 shadow-sm text-slate-200 no-print">
      <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Decision Traceability Timeline</h3>
      <div className="flex flex-wrap items-center gap-y-3">
        {steps.map((step, idx) => (
          <div key={idx} className="flex items-center">
            <div className={`flex flex-col items-start px-3 py-2 rounded-lg border ${step.status === 'warning' ? 'bg-amber-900/20 border-amber-800/50 text-amber-200' : 'bg-slate-900/50 border-slate-700 text-slate-300'}`}>
              <div className="flex items-center gap-1.5 mb-1 whitespace-nowrap">
                 {step.status === 'warning' ? <AlertCircle className="w-4 h-4 text-amber-500" /> : <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
                 <span className="text-sm font-medium">{step.title}</span>
              </div>
              <div className="text-xs opacity-75">{step.detail}</div>
            </div>
            {idx < steps.length - 1 && (
              <ArrowRight className="w-4 h-4 text-slate-600 flex-shrink-0 mx-2" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
