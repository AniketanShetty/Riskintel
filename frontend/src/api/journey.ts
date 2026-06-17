import { apiClient } from "./client";

export type SessionResponse = { session_id: string; current_state: string };

const idempotencyHeader = () => ({ "X-Idempotency-Key": crypto.randomUUID() });

// ─── Intake ───────────────────────────────────────────────────────────────────
export interface IntakePayload {
  loan_amount: number;
  loan_term: number;
  loan_purpose: string;
  income_bracket: string;
  full_name: string;
  national_id: string;
  pincode: string;
}

export const applyIntake = async (payload: IntakePayload): Promise<SessionResponse> => {
  const { data } = await apiClient.post("/apply", payload, {
    headers: idempotencyHeader(),
  });
  return data;
};

// ─── Triage ───────────────────────────────────────────────────────────────────
export type BureauStatus = "PRIME" | "SUBPRIME" | "REJECT";

export const runTriage = async (
  sessionId: string,
  bureau_status: BureauStatus
): Promise<SessionResponse> => {
  const { data } = await apiClient.post(
    `/applications/${sessionId}/triage`,
    { bureau_status },
    { headers: idempotencyHeader() }
  );
  return data;
};

// ─── Reprompt ─────────────────────────────────────────────────────────────────
export const submitReprompt = async (
  sessionId: string,
  secondary_contact: string
): Promise<SessionResponse> => {
  const { data } = await apiClient.post(
    `/applications/${sessionId}/reprompt`,
    { secondary_contact },
    { headers: idempotencyHeader() }
  );
  return data;
};

// ─── Artifact Upload ──────────────────────────────────────────────────────────
export type ArtifactType = "AADHAAR" | "PAN" | "INCOME_PROOF" | "BANK_STATEMENT" | "FO_PHOTO";

export const submitArtifact = async (
  sessionId: string,
  artifact_type: ArtifactType,
  file_hash: string
): Promise<SessionResponse> => {
  const { data } = await apiClient.post(
    `/applications/${sessionId}/artifact`,
    { artifact_type, file_hash },
    { headers: idempotencyHeader() }
  );
  return data;
};

// ─── Optimization ─────────────────────────────────────────────────────────────
export const runOptimization = async (
  sessionId: string,
  annual_rate = 0.18
): Promise<SessionResponse> => {
  const { data } = await apiClient.post(
    `/applications/${sessionId}/optimize`,
    { annual_rate },
    { headers: idempotencyHeader() }
  );
  return data;
};

// ─── Decision Actions ─────────────────────────────────────────────────────────
export const acceptCounterOffer = async (sessionId: string): Promise<SessionResponse> => {
  const { data } = await apiClient.post(
    `/decision/${sessionId}/accept`,
    {},
    { headers: idempotencyHeader() }
  );
  return data;
};

export const rejectCounterOffer = async (sessionId: string): Promise<SessionResponse> => {
  const { data } = await apiClient.post(
    `/decision/${sessionId}/reject`,
    {},
    { headers: idempotencyHeader() }
  );
  return data;
};

export interface CoApplicantPayload {
  full_name: string;
  national_id: string;
  pincode: string;
}

export const submitCoApplicant = async (
  sessionId: string,
  payload: CoApplicantPayload
): Promise<SessionResponse> => {
  const { data } = await apiClient.post(
    `/decision/${sessionId}/coapplicant`,
    payload,
    { headers: idempotencyHeader() }
  );
  return data;
};

// ─── Webhooks (simulated via console) ────────────────────────────────────────
export type AAStatus = "SUCCESS" | "EMPTY" | "FAILED" | "TIMEOUT";

export const fireAAWebhook = async (
  sessionId: string,
  status: AAStatus,
  verified_income?: number
): Promise<SessionResponse> => {
  // Note: In real usage these are HMAC-signed. We call via proxy which adds auth.
  const { data } = await apiClient.post(
    `/webhooks/aa`,
    { session_id: sessionId, status, verified_income },
    { headers: idempotencyHeader() }
  );
  return data;
};

export type FOStatus = "SUCCESS" | "FAILED" | "PENDING";

export const fireFOWebhook = async (
  sessionId: string,
  status: FOStatus,
  verified_income?: number
): Promise<SessionResponse> => {
  const { data } = await apiClient.post(
    `/webhooks/fo`,
    { session_id: sessionId, status, verified_income },
    { headers: idempotencyHeader() }
  );
  return data;
};
