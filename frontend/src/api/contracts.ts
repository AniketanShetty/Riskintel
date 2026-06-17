export interface ApplicationListResponse {
  id: string;
  current_state: string;
  loan_amount: number;
  created_at: string;
}

export interface PaginatedApplicationList {
  items: ApplicationListResponse[];
  total: number;
  limit: number;
  skip: number;
}

export type LoanTerm = 12 | 24 | 36 | 48 | 60;
export type LoanPurpose = "education" | "medical" | "home_renovation" | "wedding" | "working_capital" | "debt_consolidation";
export type IncomeBracket = "0-10k" | "10k-20k" | "20k-30k" | "30k-40k" | "40k-50k" | "50k+";
export type BureauGateStatus = "PRIME" | "SUBPRIME" | "REJECT";

export interface ApprovedTerms {
  final_loan_amount: number;
  final_tenure_months: number;
  monthly_emi: number;
  next_steps: string;
}

export interface CounterOffer {
  reason: string;
  proposed_loan_amount: number;
  proposed_tenure_months: number;
  proposed_monthly_emi: number;
}

export interface RejectionDetails {
  reason: string;
  actionable_advice: string;
}

export interface RepromptRequirements {
  missing_fields: string[];
  instructions: string;
}

export interface DecisionExplanation {
  approved_terms?: ApprovedTerms;
  counter_offer?: CounterOffer;
  rejection_details?: RejectionDetails;
  reprompt_requirements?: RepromptRequirements;
}

export interface ApplicationDetailResponse {
  id: string;
  current_state: string;
  loan_amount: number;
  loan_term: LoanTerm;
  loan_purpose: LoanPurpose;
  income_bracket: IncomeBracket;
  bureau_gate_status: BureauGateStatus | null;
  triage_pass: boolean | null;
  created_at: string;
  updated_at: string;
  explanation?: DecisionExplanation;
}

export interface DeadLetterResponse {
  id: string;
  session_id: string | null;
  route: string;
  raw_payload: string;
  failure_reason: string;
  error_details: string | null;
  occurred_at: string;
}

export interface PaginatedDeadLetterList {
  items: DeadLetterResponse[];
  total: number;
  limit: number;
  skip: number;
}
