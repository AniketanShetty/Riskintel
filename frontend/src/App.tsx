import { useState, useCallback } from "react";
import axios from "axios";

// ─── API Client ────────────────────────────────────────────────────────────────

const API_KEY = import.meta.env.VITE_API_KEY || "compose-demo-api-key";
const WEBHOOK_SECRET = import.meta.env.VITE_WEBHOOK_SECRET || "compose-demo-webhook-secret";

const http = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
});

const idempKey = () => ({ "X-Idempotency-Key": crypto.randomUUID() });

// Generate HMAC-SHA256 signature for webhook calls
async function signWebhook(body: string): Promise<{ timestamp: string; signature: string }> {
  const timestamp = String(Math.floor(Date.now() / 1000));
  const message = timestamp + "." + body;
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(WEBHOOK_SECRET),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(message));
  const hex = Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return { timestamp, signature: "sha256=" + hex };
}

async function postWebhook(path: string, payload: object) {
  const body = JSON.stringify(payload);
  const { timestamp, signature } = await signWebhook(body);
  const { data } = await http.post(path, payload, {
    headers: {
      "X-Timestamp": timestamp,
      "X-Hub-Signature-256": signature,
      "Content-Type": "application/json",
    },
  });
  return data;
}

// ─── Types ─────────────────────────────────────────────────────────────────────

interface Session {
  id: string;
  current_state: string;
  loan_amount: number;
  loan_term: number;
  loan_purpose: string;
  income_bracket: string;
  bureau_gate_status: string | null;
  triage_pass: boolean | null;
  created_at: string;
  updated_at: string;
  explanation?: {
    approved_terms?: { final_loan_amount: number; final_tenure_months: number; monthly_emi: number; next_steps: string };
    counter_offer?: { reason: string; proposed_loan_amount: number; proposed_tenure_months: number; proposed_monthly_emi: number };
    rejection_details?: { reason: string; actionable_advice: string };
    reprompt_requirements?: { missing_fields: string[]; instructions: string };
  };
}

// ─── State Timeline ────────────────────────────────────────────────────────────

const TIMELINE = [
  { label: "Intake",       states: ["INTAKE"] },
  { label: "Triage",       states: ["TRIAGE"] },
  { label: "Verification", states: ["VERIFICATION_AA", "VERIFICATION_FO", "FO_REPROMPT"] },
  { label: "Ready",        states: ["READY", "NEARLY_READY"] },
  { label: "Decision",     states: ["APPROVED", "REJECTED", "NOT_READY_YET"] },
];

function getTimelineStep(state: string) {
  return TIMELINE.findIndex((t) => t.states.includes(state));
}

// ─── Inline Styles ─────────────────────────────────────────────────────────────

const S = {
  page: {
    fontFamily: "'Inter', system-ui, sans-serif",
    minHeight: "100vh",
    background: "#f9fafb",
    padding: "24px",
    color: "#111827",
  } as React.CSSProperties,
  header: {
    marginBottom: "24px",
    borderBottom: "2px solid #e5e7eb",
    paddingBottom: "12px",
  } as React.CSSProperties,
  h1: { fontSize: "22px", fontWeight: 700, margin: 0 } as React.CSSProperties,
  subtitle: { color: "#6b7280", fontSize: "13px", marginTop: "2px" } as React.CSSProperties,
  grid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" } as React.CSSProperties,
  card: {
    background: "#fff",
    border: "1px solid #e5e7eb",
    borderRadius: "8px",
    padding: "20px",
    marginBottom: "20px",
  } as React.CSSProperties,
  cardTitle: { fontSize: "13px", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.05em", color: "#6b7280", marginBottom: "14px", margin: "0 0 14px 0" },
  label: { display: "block", fontSize: "13px", fontWeight: 500, marginBottom: "4px", color: "#374151" } as React.CSSProperties,
  input: {
    width: "100%",
    padding: "8px 10px",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
    fontSize: "14px",
    boxSizing: "border-box" as const,
    marginBottom: "12px",
    background: "#fff",
  } as React.CSSProperties,
  select: {
    width: "100%",
    padding: "8px 10px",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
    fontSize: "14px",
    boxSizing: "border-box" as const,
    marginBottom: "12px",
    background: "#fff",
  } as React.CSSProperties,
  btn: (color: string, disabled?: boolean) => ({
    padding: "9px 16px",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: 600,
    cursor: disabled ? "not-allowed" : "pointer",
    border: "none",
    background: disabled ? "#e5e7eb" : color,
    color: disabled ? "#9ca3af" : "#fff",
    opacity: disabled ? 0.7 : 1,
  } as React.CSSProperties),
  row: { display: "flex", gap: "10px", flexWrap: "wrap" as const },
  kv: { display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #f3f4f6", fontSize: "14px" } as React.CSSProperties,
  error: { background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "6px", padding: "10px 14px", color: "#b91c1c", fontSize: "13px", marginBottom: "12px" } as React.CSSProperties,
  success: { background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "6px", padding: "10px 14px", color: "#166534", fontSize: "13px", marginBottom: "12px" } as React.CSSProperties,
  code: { fontFamily: "monospace", fontSize: "12px", background: "#f3f4f6", borderRadius: "4px", padding: "2px 6px" } as React.CSSProperties,
  stateBadge: (color: string) => ({
    display: "inline-block",
    padding: "3px 10px",
    borderRadius: "999px",
    fontSize: "12px",
    fontWeight: 700,
    background: color,
    color: "#fff",
    letterSpacing: "0.04em",
  } as React.CSSProperties),
  timelineWrap: { display: "flex", alignItems: "center", gap: "0", overflowX: "auto" as const } as React.CSSProperties,
  timelineStep: (active: boolean, done: boolean) => ({
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    flex: "1",
    minWidth: "80px",
  }),
  timelineDot: (active: boolean, done: boolean) => ({
    width: "28px",
    height: "28px",
    borderRadius: "50%",
    background: active ? "#2563eb" : done ? "#16a34a" : "#e5e7eb",
    color: active || done ? "#fff" : "#9ca3af",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "12px",
    fontWeight: 700,
    border: active ? "2px solid #1d4ed8" : "2px solid transparent",
    zIndex: 1,
  } as React.CSSProperties),
  timelineLabel: (active: boolean, done: boolean) => ({
    fontSize: "11px",
    fontWeight: active ? 700 : 500,
    color: active ? "#2563eb" : done ? "#16a34a" : "#9ca3af",
    marginTop: "6px",
    textAlign: "center" as const,
  }),
  timelineLine: (done: boolean) => ({
    flex: 1,
    height: "2px",
    background: done ? "#16a34a" : "#e5e7eb",
    marginTop: "-20px",
  } as React.CSSProperties),
};

function stateColor(state: string) {
  if (["APPROVED", "READY"].includes(state)) return "#16a34a";
  if (["REJECTED", "NOT_READY_YET"].includes(state)) return "#dc2626";
  if (["NEARLY_READY"].includes(state)) return "#d97706";
  if (["VERIFICATION_AA", "VERIFICATION_FO", "FO_REPROMPT"].includes(state)) return "#7c3aed";
  if (state === "TRIAGE") return "#2563eb";
  return "#6b7280";
}

// ─── Main Component ────────────────────────────────────────────────────────────

export default function App() {
  // Form state
  const [form, setForm] = useState({
    full_name: "Demo User",
    loan_amount: "50000",
    loan_term: "12",
    loan_purpose: "medical",
    income_bracket: "50k+",
    national_id: "999-00-1234",
    pincode: "94105",
  });

  // Session state
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ type: "error" | "success"; text: string } | null>(null);

  // Co-applicant fields
  const [coApp, setCoApp] = useState({ full_name: "Jane Smith", national_id: "888-00-9999", pincode: "94105" });
  const [bureauStatus, setBureauStatus] = useState("PRIME");
  const [verifyIncome, setVerifyIncome] = useState("60000");

  const notify = (type: "error" | "success", text: string) => {
    setMsg({ type, text });
    setTimeout(() => setMsg(null), 6000);
  };

  const refreshSession = useCallback(async (id: string) => {
    const { data } = await http.get<Session>(`/applications/${id}`);
    setSession(data);
    return data;
  }, []);

  // ── SECTION 1: Create Application ──────────────────────────────────────────

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMsg(null);
    try {
      const { data } = await http.post(
        "/apply",
        { ...form, loan_amount: Number(form.loan_amount), loan_term: Number(form.loan_term) },
        { headers: idempKey() }
      );
      const sess = await refreshSession(data.session_id);
      notify("success", `Session created → ${sess.current_state}`);
    } catch (err: any) {
      notify("error", err?.response?.data?.details || err?.response?.data?.message || err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── SECTION 3: Workflow Actions ─────────────────────────────────────────────

  const runAction = async (fn: () => Promise<any>, label: string) => {
    if (!session) return;
    setLoading(true);
    setMsg(null);
    try {
      await fn();
      const sess = await refreshSession(session.id);
      notify("success", `${label} → ${sess.current_state}`);
    } catch (err: any) {
      notify("error", err?.response?.data?.details || err?.response?.data?.message || err.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleTriage = () =>
    runAction(async () => {
      await http.post(`/applications/${session!.id}/triage`, { bureau_status: bureauStatus }, { headers: idempKey() });
    }, "Triage");

  const handleVerifyIncome = () =>
    runAction(async () => {
      const state = session!.current_state;
      const income = Number(verifyIncome) || undefined;
      if (state === "VERIFICATION_AA" || state === "TRIAGE") {
        await postWebhook("/webhooks/aa", { session_id: session!.id, status: "SUCCESS", verified_income: income });
      } else if (state === "VERIFICATION_FO" || state === "FO_REPROMPT") {
        await postWebhook("/webhooks/fo", { session_id: session!.id, status: "VERIFIED_CLEAN", verified_income: income });
      } else {
        // Try AA first, then FO
        try {
          await postWebhook("/webhooks/aa", { session_id: session!.id, status: "SUCCESS", verified_income: income });
        } catch {
          await postWebhook("/webhooks/fo", { session_id: session!.id, status: "VERIFIED_CLEAN", verified_income: income });
        }
      }
    }, "Verify Income");

  const handleOptimize = () =>
    runAction(async () => {
      await http.post(`/applications/${session!.id}/optimize`, { annual_rate: 0.18 }, { headers: idempKey() });
    }, "Optimize");

  const handleCoApplicant = () =>
    runAction(async () => {
      await http.post(`/decision/${session!.id}/coapplicant`, coApp, { headers: idempKey() });
    }, "Add Co-Applicant");

  const handleAccept = () =>
    runAction(async () => {
      await http.post(`/decision/${session!.id}/accept`, {}, { headers: idempKey() });
    }, "Accept Counter-Offer");

  const handleReject = () =>
    runAction(async () => {
      await http.post(`/decision/${session!.id}/reject`, {}, { headers: idempKey() });
    }, "Reject Counter-Offer");

  // ── State helpers ──────────────────────────────────────────────────────────

  const state = session?.current_state ?? "";
  const timelineStep = getTimelineStep(state);
  const isTerminal = ["APPROVED", "REJECTED", "NOT_READY_YET"].includes(state);

  const canTriage = state === "TRIAGE";
  const canVerify = ["VERIFICATION_AA", "VERIFICATION_FO", "FO_REPROMPT"].includes(state);
  const canOptimize = ["READY", "NEARLY_READY"].includes(state);
  const canCoApp = ["REJECTED", "NOT_READY_YET"].includes(state);
  const canAccept = state === "NEARLY_READY";

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div style={S.page}>
      <div style={{ maxWidth: "960px", margin: "0 auto" }}>

        {/* Header */}
        <div style={S.header}>
          <h1 style={S.h1}>🏦 RiskIntel Demo Console</h1>
          <div style={S.subtitle}>End-to-end FSM workflow demonstration</div>
        </div>

        {/* Notification */}
        {msg && (
          <div style={msg.type === "error" ? S.error : S.success}>
            {msg.type === "error" ? "⚠ " : "✓ "}{msg.text}
          </div>
        )}

        <div style={S.grid}>
          {/* ── LEFT COLUMN ───────────────────────────────────────────────── */}
          <div>

            {/* SECTION 1 — Create Application */}
            <div style={S.card}>
              <p style={S.cardTitle}>Section 1 — Create Application</p>
              <form onSubmit={handleCreate}>
                <label style={S.label}>Full Name</label>
                <input style={S.input} value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} required />

                <label style={S.label}>Loan Amount ($)</label>
                <input style={S.input} type="number" min="1000" max="500000" value={form.loan_amount} onChange={e => setForm(f => ({ ...f, loan_amount: e.target.value }))} required />

                <label style={S.label}>Loan Term</label>
                <select style={S.select} value={form.loan_term} onChange={e => setForm(f => ({ ...f, loan_term: e.target.value }))}>
                  <option value="12">12 months</option>
                  <option value="24">24 months</option>
                  <option value="36">36 months</option>
                  <option value="48">48 months</option>
                  <option value="60">60 months</option>
                </select>

                <label style={S.label}>Loan Purpose</label>
                <select style={S.select} value={form.loan_purpose} onChange={e => setForm(f => ({ ...f, loan_purpose: e.target.value }))}>
                  <option value="education">Education</option>
                  <option value="medical">Medical</option>
                  <option value="home_renovation">Home Renovation</option>
                  <option value="wedding">Wedding</option>
                  <option value="working_capital">Working Capital</option>
                  <option value="debt_consolidation">Debt Consolidation</option>
                </select>

                <label style={S.label}>Income Bracket</label>
                <select style={S.select} value={form.income_bracket} onChange={e => setForm(f => ({ ...f, income_bracket: e.target.value }))}>
                  <option value="0-10k">$0 – $10,000</option>
                  <option value="10k-20k">$10,000 – $20,000</option>
                  <option value="20k-30k">$20,000 – $30,000</option>
                  <option value="30k-40k">$30,000 – $40,000</option>
                  <option value="40k-50k">$40,000 – $50,000</option>
                  <option value="50k+">$50,000+</option>
                </select>

                <button type="submit" disabled={loading} style={S.btn("#2563eb", loading)}>
                  {loading ? "Working…" : "Create Application"}
                </button>
              </form>
            </div>

            {/* SECTION 3 — Workflow Actions */}
            {session && (
              <div style={S.card}>
                <p style={S.cardTitle}>Section 3 — Workflow Actions</p>

                {/* Run Triage */}
                <div style={{ marginBottom: "14px" }}>
                  <label style={S.label}>Bureau Status</label>
                  <select style={{ ...S.select, marginBottom: "8px" }} value={bureauStatus} onChange={e => setBureauStatus(e.target.value)}>
                    <option value="PRIME">PRIME</option>
                    <option value="SUBPRIME">SUBPRIME</option>
                    <option value="REJECT">REJECT</option>
                  </select>
                  <button onClick={handleTriage} disabled={loading || !canTriage} style={S.btn("#2563eb", loading || !canTriage)}>
                    Run Triage
                  </button>
                  {!canTriage && state && <span style={{ marginLeft: 8, fontSize: 12, color: "#9ca3af" }}>requires TRIAGE state</span>}
                </div>

                {/* Verify Income */}
                <div style={{ marginBottom: "14px" }}>
                  <label style={S.label}>Verified Income ($)</label>
                  <input
                    style={{ ...S.input, marginBottom: "8px" }}
                    type="number"
                    value={verifyIncome}
                    onChange={e => setVerifyIncome(e.target.value)}
                  />
                  <button onClick={handleVerifyIncome} disabled={loading || !canVerify} style={S.btn("#7c3aed", loading || !canVerify)}>
                    Verify Income
                  </button>
                  {!canVerify && state && <span style={{ marginLeft: 8, fontSize: 12, color: "#9ca3af" }}>requires VERIFICATION_AA/FO state</span>}
                </div>

                {/* Optimize */}
                <div style={{ marginBottom: "14px" }}>
                  <button onClick={handleOptimize} disabled={loading || !canOptimize} style={S.btn("#059669", loading || !canOptimize)}>
                    Optimize (rate: 18%)
                  </button>
                  {!canOptimize && state && <span style={{ marginLeft: 8, fontSize: 12, color: "#9ca3af" }}>requires READY / NEARLY_READY</span>}
                </div>

                {/* Counter-offer actions */}
                {canAccept && (
                  <div style={{ marginBottom: "14px" }}>
                    <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6, color: "#d97706" }}>Counter-Offer Decision</div>
                    <div style={S.row}>
                      <button onClick={handleAccept} disabled={loading} style={S.btn("#16a34a", loading)}>✓ Accept</button>
                      <button onClick={handleReject} disabled={loading} style={S.btn("#dc2626", loading)}>✗ Reject</button>
                    </div>
                  </div>
                )}

                {/* Add Co-Applicant */}
                <div style={{ marginBottom: "0" }}>
                  <label style={S.label}>Co-Applicant Name</label>
                  <input style={S.input} value={coApp.full_name} onChange={e => setCoApp(c => ({ ...c, full_name: e.target.value }))} />
                  <label style={S.label}>Co-Applicant ID</label>
                  <input style={S.input} value={coApp.national_id} onChange={e => setCoApp(c => ({ ...c, national_id: e.target.value }))} />
                  <button onClick={handleCoApplicant} disabled={loading || !canCoApp} style={S.btn("#d97706", loading || !canCoApp)}>
                    Add Co-Applicant
                  </button>
                  {!canCoApp && state && <span style={{ marginLeft: 8, fontSize: 12, color: "#9ca3af" }}>requires REJECTED / NOT_READY_YET</span>}
                </div>
              </div>
            )}
          </div>

          {/* ── RIGHT COLUMN ──────────────────────────────────────────────── */}
          <div>

            {/* SECTION 2 — Current Session */}
            <div style={S.card}>
              <p style={S.cardTitle}>Section 2 — Current Session</p>
              {!session ? (
                <div style={{ color: "#9ca3af", fontSize: 14 }}>No session yet. Create an application to begin.</div>
              ) : (
                <>
                  <div style={S.kv}>
                    <span style={{ color: "#6b7280" }}>Session ID</span>
                    <span style={S.code}>{session.id.slice(0, 18)}…</span>
                  </div>
                  <div style={S.kv}>
                    <span style={{ color: "#6b7280" }}>Current State</span>
                    <span style={S.stateBadge(stateColor(session.current_state))}>{session.current_state}</span>
                  </div>
                  <div style={S.kv}>
                    <span style={{ color: "#6b7280" }}>Loan Amount</span>
                    <span>${session.loan_amount.toLocaleString()}</span>
                  </div>
                  <div style={S.kv}>
                    <span style={{ color: "#6b7280" }}>Term</span>
                    <span>{session.loan_term} months</span>
                  </div>
                  <div style={S.kv}>
                    <span style={{ color: "#6b7280" }}>Purpose</span>
                    <span style={{ textTransform: "capitalize" }}>{session.loan_purpose.replace(/_/g, " ")}</span>
                  </div>
                  <div style={S.kv}>
                    <span style={{ color: "#6b7280" }}>Income Bracket</span>
                    <span>{session.income_bracket}</span>
                  </div>
                  <div style={S.kv}>
                    <span style={{ color: "#6b7280" }}>Bureau Gate</span>
                    <span>{session.bureau_gate_status ?? "—"}</span>
                  </div>
                  <div style={{ ...S.kv, borderBottom: "none" }}>
                    <span style={{ color: "#6b7280" }}>Triage Pass</span>
                    <span>{session.triage_pass === null ? "—" : session.triage_pass ? "Yes" : "No"}</span>
                  </div>
                  <button
                    onClick={() => refreshSession(session.id).then(s => notify("success", `Refreshed → ${s.current_state}`))}
                    style={{ ...S.btn("#6b7280"), marginTop: 12, fontSize: 12 }}
                    disabled={loading}
                  >
                    ↻ Refresh
                  </button>
                </>
              )}
            </div>

            {/* SECTION 4 — State Timeline */}
            {session && (
              <div style={S.card}>
                <p style={S.cardTitle}>Section 4 — State Timeline</p>
                <div style={{ display: "flex", alignItems: "flex-start" }}>
                  {TIMELINE.map((step, i) => {
                    const active = i === timelineStep;
                    const done = i < timelineStep;
                    return (
                      <div key={step.label} style={{ display: "flex", alignItems: "flex-start", flex: 1 }}>
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1 }}>
                          <div style={S.timelineDot(active, done)}>
                            {done ? "✓" : i + 1}
                          </div>
                          <div style={S.timelineLabel(active, done)}>{step.label}</div>
                        </div>
                        {i < TIMELINE.length - 1 && (
                          <div style={{ flex: 1, height: "2px", background: done ? "#16a34a" : "#e5e7eb", marginTop: "14px" }} />
                        )}
                      </div>
                    );
                  })}
                </div>
                {isTerminal && (
                  <div style={{ marginTop: 14, padding: "8px 12px", borderRadius: 6, background: stateColor(state) + "18", border: `1px solid ${stateColor(state)}44`, color: stateColor(state), fontSize: 13, fontWeight: 600 }}>
                    Terminal State: {state}
                  </div>
                )}
              </div>
            )}

            {/* SECTION 5 — Decision Output */}
            {session?.explanation && (
              <div style={S.card}>
                <p style={S.cardTitle}>Section 5 — Decision Output</p>

                {session.explanation.approved_terms && (
                  <div style={{ background: "#f0fdf4", border: "1px solid #86efac", borderRadius: 6, padding: "12px 14px", marginBottom: 10 }}>
                    <div style={{ fontWeight: 700, color: "#15803d", marginBottom: 6 }}>✓ Approved Terms</div>
                    <div style={S.kv}><span style={{ color: "#6b7280" }}>Loan Amount</span><span>${session.explanation.approved_terms.final_loan_amount.toLocaleString()}</span></div>
                    <div style={S.kv}><span style={{ color: "#6b7280" }}>Tenure</span><span>{session.explanation.approved_terms.final_tenure_months} months</span></div>
                    <div style={{ ...S.kv, borderBottom: "none" }}><span style={{ color: "#6b7280" }}>Monthly EMI</span><span style={{ fontWeight: 700 }}>${session.explanation.approved_terms.monthly_emi.toLocaleString()}</span></div>
                    {session.explanation.approved_terms.next_steps && (
                      <div style={{ marginTop: 8, fontSize: 13, color: "#15803d" }}>{session.explanation.approved_terms.next_steps}</div>
                    )}
                  </div>
                )}

                {session.explanation.counter_offer && (
                  <div style={{ background: "#fffbeb", border: "1px solid #fcd34d", borderRadius: 6, padding: "12px 14px", marginBottom: 10 }}>
                    <div style={{ fontWeight: 700, color: "#b45309", marginBottom: 6 }}>⚡ Counter-Offer</div>
                    <div style={{ fontSize: 13, color: "#92400e", marginBottom: 8 }}>{session.explanation.counter_offer.reason}</div>
                    <div style={S.kv}><span style={{ color: "#6b7280" }}>Proposed Amount</span><span>${session.explanation.counter_offer.proposed_loan_amount.toLocaleString()}</span></div>
                    <div style={S.kv}><span style={{ color: "#6b7280" }}>Tenure</span><span>{session.explanation.counter_offer.proposed_tenure_months} months</span></div>
                    <div style={{ ...S.kv, borderBottom: "none" }}><span style={{ color: "#6b7280" }}>Monthly EMI</span><span style={{ fontWeight: 700 }}>${session.explanation.counter_offer.proposed_monthly_emi.toLocaleString()}</span></div>
                  </div>
                )}

                {session.explanation.rejection_details && (
                  <div style={{ background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 6, padding: "12px 14px", marginBottom: 10 }}>
                    <div style={{ fontWeight: 700, color: "#b91c1c", marginBottom: 6 }}>✗ Rejection</div>
                    <div style={{ fontSize: 13, color: "#991b1b", marginBottom: 6 }}>{session.explanation.rejection_details.reason}</div>
                    <div style={{ fontSize: 13, color: "#6b7280" }}>{session.explanation.rejection_details.actionable_advice}</div>
                  </div>
                )}

                {session.explanation.reprompt_requirements && (
                  <div style={{ background: "#fdf4ff", border: "1px solid #e879f9", borderRadius: 6, padding: "12px 14px" }}>
                    <div style={{ fontWeight: 700, color: "#7e22ce", marginBottom: 6 }}>↺ Reprompt Required</div>
                    <div style={{ fontSize: 13, color: "#6b21a8" }}>Missing: {session.explanation.reprompt_requirements.missing_fields.join(", ")}</div>
                    <div style={{ fontSize: 13, color: "#6b7280", marginTop: 4 }}>{session.explanation.reprompt_requirements.instructions}</div>
                  </div>
                )}

                {!session.explanation.approved_terms && !session.explanation.counter_offer && !session.explanation.rejection_details && !session.explanation.reprompt_requirements && (
                  <div style={{ color: "#9ca3af", fontSize: 14 }}>No decision output yet for state: <strong>{state}</strong></div>
                )}
              </div>
            )}
            {session && !session.explanation && (
              <div style={S.card}>
                <p style={S.cardTitle}>Section 5 — Decision Output</p>
                <div style={{ color: "#9ca3af", fontSize: 14 }}>No decision output yet. Complete the workflow to see results.</div>
              </div>
            )}

          </div>
        </div>

        {/* Footer */}
        <div style={{ textAlign: "center", color: "#9ca3af", fontSize: 12, marginTop: 8 }}>
          RiskIntel V2 · FSM Demo · Backend: http://localhost:8000
        </div>
      </div>
    </div>
  );
}
