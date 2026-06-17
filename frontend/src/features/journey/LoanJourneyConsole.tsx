import { useState, useRef, useEffect, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Terminal,
  Zap,
  RefreshCw,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Activity,
  User,
  CreditCard,
  FileText,
  Copy,
  Check,
  Loader2,
  ArrowRight,
  ShieldCheck,
  GitBranch,
} from "lucide-react";
import { getApplication, getApplications, createApplication } from "@/api/applications";
import type { ApplicationDetailResponse } from "@/api/contracts";
import {
  runTriage,
  submitReprompt,
  submitArtifact,
  runOptimization,
  acceptCounterOffer,
  rejectCounterOffer,
  submitCoApplicant,
  fireAAWebhook,
  fireFOWebhook,
  type BureauStatus,
  type AAStatus,
  type FOStatus,
  type ArtifactType,
} from "@/api/journey";

// ─── Types ────────────────────────────────────────────────────────────────────

interface LogEntry {
  id: string;
  ts: string;
  type: "info" | "success" | "error" | "action" | "state";
  message: string;
  detail?: string;
}

interface ActionField {
  key: string;
  label: string;
  type: "select" | "text" | "number";
  options?: string[];
  defaultValue?: string | number;
  placeholder?: string;
}

interface ActionDef {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
  variant: "primary" | "success" | "danger" | "warning" | "ghost";
  fields?: ActionField[];
  validStates: string[];
  handler: (sessionId: string, params: Record<string, string>) => Promise<{ current_state: string }>;
}

// ─── FSM State Config ─────────────────────────────────────────────────────────

const STATE_META: Record<string, { color: string; bg: string; icon: React.ElementType; label: string }> = {
  INTAKE:            { color: "text-sky-400",    bg: "bg-sky-900/30 border-sky-700/50",     icon: FileText,     label: "Intake" },
  TRIAGE:            { color: "text-violet-400", bg: "bg-violet-900/30 border-violet-700/50", icon: GitBranch,  label: "Triage" },
  VERIFICATION_AA:   { color: "text-amber-400",  bg: "bg-amber-900/30 border-amber-700/50",  icon: ShieldCheck, label: "AA Verification" },
  VERIFICATION_FO:   { color: "text-amber-400",  bg: "bg-amber-900/30 border-amber-700/50",  icon: ShieldCheck, label: "FO Verification" },
  FO_REPROMPT:       { color: "text-orange-400", bg: "bg-orange-900/30 border-orange-700/50", icon: AlertTriangle, label: "FO Reprompt" },
  READY:             { color: "text-emerald-400", bg: "bg-emerald-900/30 border-emerald-700/50", icon: CheckCircle2, label: "Ready" },
  NEARLY_READY:      { color: "text-blue-400",   bg: "bg-blue-900/30 border-blue-700/50",   icon: Activity,    label: "Nearly Ready" },
  NOT_READY_YET:     { color: "text-red-400",    bg: "bg-red-900/30 border-red-700/50",     icon: XCircle,     label: "Not Ready Yet" },
  REJECTED:          { color: "text-red-500",    bg: "bg-red-950/40 border-red-800/50",     icon: XCircle,     label: "Rejected" },
  APPROVED:          { color: "text-emerald-300", bg: "bg-emerald-950/40 border-emerald-700/50", icon: CheckCircle2, label: "Approved" },
};

const FALLBACK_META = { color: "text-slate-400", bg: "bg-slate-800/50 border-slate-700/50", icon: Clock, label: "Unknown" };

// ─── Action Definitions (mapped to FSM transitions) ───────────────────────────

const ACTIONS: ActionDef[] = [
  // ── Triage ──
  {
    id: "triage_prime",
    label: "Run Triage → PRIME",
    description: "Bureau check returns PRIME status",
    icon: CheckCircle2,
    variant: "success",
    validStates: ["TRIAGE"],
    fields: [],
    handler: (id) => runTriage(id, "PRIME"),
  },
  {
    id: "triage_subprime",
    label: "Run Triage → SUBPRIME",
    description: "Bureau check returns SUBPRIME status",
    icon: AlertTriangle,
    variant: "warning",
    validStates: ["TRIAGE"],
    fields: [],
    handler: (id) => runTriage(id, "SUBPRIME"),
  },
  {
    id: "triage_reject",
    label: "Run Triage → REJECT",
    description: "Bureau hard-rejects this applicant",
    icon: XCircle,
    variant: "danger",
    validStates: ["TRIAGE"],
    fields: [],
    handler: (id) => runTriage(id, "REJECT"),
  },
  // ── AA Webhook ──
  {
    id: "aa_success",
    label: "Fire AA Webhook → SUCCESS",
    description: "Account aggregator returns verified income",
    icon: Zap,
    variant: "success",
    validStates: ["VERIFICATION_AA"],
    fields: [
      { key: "verified_income", label: "Verified Income ($)", type: "number", defaultValue: 75000, placeholder: "75000" },
    ],
    handler: (id, p) => fireAAWebhook(id, "SUCCESS", Number(p.verified_income)),
  },
  {
    id: "aa_empty",
    label: "Fire AA Webhook → EMPTY",
    description: "No data returned by aggregator",
    icon: AlertTriangle,
    variant: "warning",
    validStates: ["VERIFICATION_AA"],
    fields: [],
    handler: (id) => fireAAWebhook(id, "EMPTY"),
  },
  {
    id: "aa_failed",
    label: "Fire AA Webhook → FAILED",
    description: "Aggregator call failed",
    icon: XCircle,
    variant: "danger",
    validStates: ["VERIFICATION_AA"],
    fields: [],
    handler: (id) => fireAAWebhook(id, "FAILED"),
  },
  {
    id: "aa_timeout",
    label: "Fire AA Webhook → TIMEOUT",
    description: "Aggregator timed out",
    icon: Clock,
    variant: "ghost",
    validStates: ["VERIFICATION_AA"],
    fields: [],
    handler: (id) => fireAAWebhook(id, "TIMEOUT"),
  },
  // ── FO Webhook ──
  {
    id: "fo_success",
    label: "Fire FO Webhook → SUCCESS",
    description: "Field officer verified the applicant",
    icon: Zap,
    variant: "success",
    validStates: ["VERIFICATION_FO", "FO_REPROMPT"],
    fields: [
      { key: "verified_income", label: "Verified Income ($)", type: "number", defaultValue: 60000, placeholder: "60000" },
    ],
    handler: (id, p) => fireFOWebhook(id, "SUCCESS", Number(p.verified_income)),
  },
  {
    id: "fo_failed",
    label: "Fire FO Webhook → FAILED",
    description: "Field officer verification failed",
    icon: XCircle,
    variant: "danger",
    validStates: ["VERIFICATION_FO", "FO_REPROMPT"],
    fields: [],
    handler: (id) => fireFOWebhook(id, "FAILED"),
  },
  // ── Reprompt ──
  {
    id: "reprompt",
    label: "Submit Reprompt Data",
    description: "Provide secondary contact to unlock FO re-verification",
    icon: RefreshCw,
    variant: "warning",
    validStates: ["FO_REPROMPT"],
    fields: [
      { key: "secondary_contact", label: "Secondary Contact", type: "text", defaultValue: "+1-555-0100", placeholder: "+1-555-0100" },
    ],
    handler: (id, p) => submitReprompt(id, p.secondary_contact),
  },
  // ── Artifact ──
  {
    id: "artifact",
    label: "Submit Artifact",
    description: "Upload a document artifact for verification",
    icon: FileText,
    variant: "ghost",
    validStates: ["VERIFICATION_AA", "VERIFICATION_FO", "FO_REPROMPT", "TRIAGE"],
    fields: [
      {
        key: "artifact_type",
        label: "Artifact Type",
        type: "select",
        options: ["AADHAAR", "PAN", "INCOME_PROOF", "BANK_STATEMENT", "FO_PHOTO"],
        defaultValue: "AADHAAR",
      },
      { key: "file_hash", label: "File Hash (SHA-256)", type: "text", defaultValue: "abc123def456", placeholder: "sha256-hash" },
    ],
    handler: (id, p) => submitArtifact(id, p.artifact_type as ArtifactType, p.file_hash),
  },
  // ── Optimization ──
  {
    id: "optimize",
    label: "Run Optimization",
    description: "Compute EMI schedule and loan terms",
    icon: Activity,
    variant: "primary",
    validStates: ["READY", "NEARLY_READY"],
    fields: [
      { key: "annual_rate", label: "Annual Rate (e.g. 0.18)", type: "number", defaultValue: 0.18, placeholder: "0.18" },
    ],
    handler: (id, p) => runOptimization(id, Number(p.annual_rate)),
  },
  // ── Counter-Offer Decision ──
  {
    id: "accept",
    label: "Accept Counter-Offer",
    description: "Applicant accepts the proposed loan terms",
    icon: CheckCircle2,
    variant: "success",
    validStates: ["NEARLY_READY"],
    fields: [],
    handler: (id) => acceptCounterOffer(id),
  },
  {
    id: "reject_offer",
    label: "Reject Counter-Offer",
    description: "Applicant declines the proposed terms",
    icon: XCircle,
    variant: "danger",
    validStates: ["NEARLY_READY"],
    fields: [],
    handler: (id) => rejectCounterOffer(id),
  },
  // ── Co-Applicant ──
  {
    id: "coapplicant",
    label: "Submit Co-Applicant",
    description: "Add a co-applicant to repair thin credit file",
    icon: User,
    variant: "primary",
    validStates: ["REJECTED", "NOT_READY_YET"],
    fields: [
      { key: "full_name", label: "Co-Applicant Full Name", type: "text", defaultValue: "Jane Smith", placeholder: "Full Name" },
      { key: "national_id", label: "National ID", type: "text", defaultValue: "888-00-9999", placeholder: "ID Number" },
      { key: "pincode", label: "Pincode / ZIP", type: "text", defaultValue: "94105", placeholder: "94105" },
    ],
    handler: (id, p) => submitCoApplicant(id, { full_name: p.full_name, national_id: p.national_id, pincode: p.pincode }),
  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmtTime = () => new Date().toISOString().slice(11, 23);

const mkLog = (type: LogEntry["type"], message: string, detail?: string): LogEntry => ({
  id: crypto.randomUUID(),
  ts: fmtTime(),
  type,
  message,
  detail,
});

// ─── Sub-Components ───────────────────────────────────────────────────────────

function StateBadge({ state }: { state: string }) {
  const meta = STATE_META[state] ?? FALLBACK_META;
  const Icon = meta.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-bold tracking-widest uppercase ${meta.color} ${meta.bg}`}>
      <Icon className="w-3 h-3" />
      {meta.label}
    </span>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={handleCopy}
      className="ml-2 p-1 rounded text-slate-500 hover:text-slate-300 hover:bg-slate-700 transition-colors"
      title="Copy to clipboard"
    >
      {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
    </button>
  );
}

function LogLine({ entry }: { entry: LogEntry }) {
  const colors: Record<LogEntry["type"], string> = {
    info: "text-slate-400",
    success: "text-emerald-400",
    error: "text-red-400",
    action: "text-sky-400",
    state: "text-violet-400 font-bold",
  };
  const prefix: Record<LogEntry["type"], string> = {
    info: "   ",
    success: "✓  ",
    error: "✗  ",
    action: "→  ",
    state: "★  ",
  };
  return (
    <div className={`font-mono text-xs leading-5 ${colors[entry.type]}`}>
      <span className="text-slate-600 select-none">{entry.ts} </span>
      <span className="opacity-60">{prefix[entry.type]}</span>
      <span>{entry.message}</span>
      {entry.detail && (
        <div className="ml-8 text-slate-500 truncate">{entry.detail}</div>
      )}
    </div>
  );
}

function ActionPanel({
  action,
  sessionId,
  onSuccess,
  onError,
}: {
  action: ActionDef;
  sessionId: string;
  onSuccess: (state: string, actionLabel: string) => void;
  onError: (msg: string, actionLabel: string) => void;
}) {
  const [params, setParams] = useState<Record<string, string>>(() => {
    const init: Record<string, string> = {};
    action.fields?.forEach((f) => {
      init[f.key] = String(f.defaultValue ?? "");
    });
    return init;
  });
  const [loading, setLoading] = useState(false);

  const VARIANT_STYLES: Record<ActionDef["variant"], string> = {
    primary: "bg-sky-600 hover:bg-sky-500 border-sky-500 text-white",
    success: "bg-emerald-700 hover:bg-emerald-600 border-emerald-600 text-white",
    danger: "bg-red-800 hover:bg-red-700 border-red-700 text-white",
    warning: "bg-amber-700 hover:bg-amber-600 border-amber-600 text-white",
    ghost: "bg-slate-700 hover:bg-slate-600 border-slate-600 text-slate-200",
  };

  const inputCls =
    "w-full bg-slate-900 border border-slate-700 rounded-md px-2 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/40 placeholder:text-slate-600";

  const handleRun = async () => {
    setLoading(true);
    try {
      const result = await action.handler(sessionId, params);
      onSuccess(result.current_state, action.label);
    } catch (err: any) {
      const msg =
        err?.response?.data?.details || err?.response?.data?.message || err?.message || "Unknown error";
      onError(msg, action.label);
    } finally {
      setLoading(false);
    }
  };

  const Icon = action.icon;

  return (
    <div className="border border-slate-700/60 bg-slate-800/40 rounded-xl p-4 hover:border-slate-600/80 transition-colors">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <div className={`p-1.5 rounded-md ${VARIANT_STYLES[action.variant].split(" ")[0]}`}>
            <Icon className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-100">{action.label}</div>
            <div className="text-xs text-slate-500">{action.description}</div>
          </div>
        </div>
      </div>

      {action.fields && action.fields.length > 0 && (
        <div className="space-y-2 mb-3">
          {action.fields.map((field) => (
            <div key={field.key}>
              <label className="block text-xs text-slate-500 mb-1">{field.label}</label>
              {field.type === "select" ? (
                <select
                  value={params[field.key]}
                  onChange={(e) => setParams((p) => ({ ...p, [field.key]: e.target.value }))}
                  className={inputCls}
                >
                  {field.options?.map((o) => (
                    <option key={o} value={o}>
                      {o}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={field.type}
                  step={field.type === "number" ? "any" : undefined}
                  value={params[field.key]}
                  onChange={(e) => setParams((p) => ({ ...p, [field.key]: e.target.value }))}
                  placeholder={field.placeholder}
                  className={inputCls}
                />
              )}
            </div>
          ))}
        </div>
      )}

      <button
        onClick={handleRun}
        disabled={loading}
        className={`w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg border transition-all ${VARIANT_STYLES[action.variant]} disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        {loading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <ArrowRight className="w-3.5 h-3.5" />
        )}
        {loading ? "Executing…" : "Execute"}
      </button>
    </div>
  );
}

// ─── New Session Form (inline intake) ────────────────────────────────────────

function NewSessionForm({ onCreated }: { onCreated: (id: string) => void }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    const fd = new FormData(e.currentTarget);
    try {
      const res = await createApplication({
        loan_amount: Number(fd.get("loan_amount")),
        loan_term: Number(fd.get("loan_term")),
        loan_purpose: fd.get("loan_purpose"),
        income_bracket: fd.get("income_bracket"),
        full_name: fd.get("full_name"),
        national_id: fd.get("national_id"),
        pincode: fd.get("pincode"),
      });
      onCreated(res.session_id);
      setOpen(false);
    } catch (err: any) {
      setError(err?.response?.data?.details || err?.message || "Failed to create application");
    } finally {
      setLoading(false);
    }
  };

  const inputCls =
    "w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/40 placeholder:text-slate-600";

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 px-4 py-2 bg-sky-700 hover:bg-sky-600 border border-sky-600 rounded-lg text-sm font-semibold text-white transition-all"
      >
        <Terminal className="w-4 h-4" />
        New Session
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl p-8">
        <h3 className="text-lg font-bold text-slate-100 mb-6 flex items-center gap-2">
          <Terminal className="w-5 h-5 text-sky-400" /> New Loan Session — Intake
        </h3>
        {error && (
          <div className="mb-4 p-3 bg-red-950/50 border border-red-800 rounded-lg text-red-400 text-xs font-mono">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Full Name</label>
              <input name="full_name" required className={inputCls} defaultValue="Demo User" />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">National ID</label>
              <input name="national_id" required className={inputCls} defaultValue="999-00-1234" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Loan Amount ($)</label>
              <input name="loan_amount" type="number" min="1000" max="500000" required className={inputCls} defaultValue={50000} />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Loan Term</label>
              <select name="loan_term" className={inputCls} defaultValue={12}>
                {[12, 24, 36, 48, 60].map((t) => (
                  <option key={t} value={t}>{t} months</option>
                ))}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Loan Purpose</label>
              <select name="loan_purpose" className={inputCls} defaultValue="medical">
                {["education", "medical", "home_renovation", "wedding", "working_capital", "debt_consolidation"].map((p) => (
                  <option key={p} value={p}>{p.replace(/_/g, " ")}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Income Bracket</label>
              <select name="income_bracket" className={inputCls} defaultValue="50k+">
                {["0-10k", "10k-20k", "20k-30k", "30k-40k", "40k-50k", "50k+"].map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Pincode</label>
            <input name="pincode" required className={inputCls} defaultValue="94105" />
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-sky-700 hover:bg-sky-600 border border-sky-600 rounded-lg text-sm font-semibold text-white transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              {loading ? "Creating…" : "Create & Load Session"}
            </button>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-sm text-slate-400 transition-all"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function LoanJourneyConsole() {
  const queryClient = useQueryClient();
  const [sessionId, setSessionId] = useState<string>("");
  const [inputId, setInputId] = useState<string>("");
  const [logs, setLogs] = useState<LogEntry[]>([
    mkLog("info", "Loan Journey Console ready. Load a session or create a new one."),
  ]);
  const [activeActionId, setActiveActionId] = useState<string | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  const { data: session, isLoading, isError, refetch } = useQuery({
    queryKey: ["journey-session", sessionId],
    queryFn: () => getApplication(sessionId),
    enabled: !!sessionId,
    staleTime: 0,
    retry: 1,
  });

  const { data: recentSessions } = useQuery({
    queryKey: ["journey-recent"],
    queryFn: () => getApplications(0, 10),
    staleTime: 30000,
  });

  const addLog = useCallback((entry: LogEntry) => {
    setLogs((prev) => [...prev.slice(-200), entry]);
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const handleLoad = (id: string) => {
    const trimmed = id.trim();
    if (!trimmed) return;
    setSessionId(trimmed);
    setInputId(trimmed);
    addLog(mkLog("action", `Loading session ${trimmed.slice(0, 16)}…`));
  };

  const handleActionSuccess = useCallback(
    (newState: string, actionLabel: string) => {
      addLog(mkLog("success", `${actionLabel} → succeeded`));
      addLog(mkLog("state", `State transitioned → ${newState}`));
      queryClient.invalidateQueries({ queryKey: ["journey-session", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["journey-recent"] });
      setActiveActionId(null);
    },
    [addLog, queryClient, sessionId]
  );

  const handleActionError = useCallback(
    (msg: string, actionLabel: string) => {
      addLog(mkLog("error", `${actionLabel} failed`, msg));
    },
    [addLog]
  );

  const currentState = session?.current_state ?? "";
  const availableActions = ACTIONS.filter((a) => a.validStates.includes(currentState));
  const stateMeta = STATE_META[currentState] ?? FALLBACK_META;
  const StateIcon = stateMeta.icon;

  // ── FSM Pipeline (linear stage tracker) ───────────────────────────────────
  const PIPELINE_STAGES = [
    { key: "INTAKE", label: "Intake" },
    { key: "TRIAGE", label: "Triage" },
    { key: "VERIFICATION_AA", label: "AA Verify" },
    { key: "VERIFICATION_FO", label: "FO Verify" },
    { key: "READY", label: "Ready" },
    { key: "NEARLY_READY", label: "Counter" },
    { key: "APPROVED", label: "Approved" },
  ];

  const stageIndex = PIPELINE_STAGES.findIndex((s) => s.key === currentState);
  const isTerminal = ["APPROVED", "REJECTED", "NOT_READY_YET"].includes(currentState);

  return (
    <div className="h-[calc(100vh-0px)] bg-slate-950 text-slate-100 flex flex-col overflow-hidden font-mono">
      {/* ── Top Bar ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-4 px-6 py-3 border-b border-slate-800 bg-slate-900/80 backdrop-blur shrink-0">
        <div className="flex items-center gap-2 text-sky-400 font-bold text-sm">
          <Terminal className="w-4 h-4" />
          Loan Journey Console
        </div>
        <div className="h-4 w-px bg-slate-700" />

        {/* Session loader */}
        <div className="flex items-center gap-2 flex-1 max-w-xl">
          <input
            type="text"
            value={inputId}
            onChange={(e) => setInputId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLoad(inputId)}
            placeholder="Paste session ID or pick from recent…"
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/40"
          />
          <button
            onClick={() => handleLoad(inputId)}
            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 border border-slate-600 rounded-lg text-xs text-slate-200 transition-all"
          >
            Load
          </button>
          {sessionId && (
            <button
              onClick={() => refetch()}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-slate-400 hover:text-slate-200 transition-all"
              title="Refresh session"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="ml-auto flex items-center gap-3">
          {session && <StateBadge state={currentState} />}
          <NewSessionForm
            onCreated={(id) => {
              addLog(mkLog("success", `Session created: ${id.slice(0, 16)}…`));
              addLog(mkLog("state", "State → TRIAGE"));
              handleLoad(id);
            }}
          />
        </div>
      </div>

      {/* ── Pipeline Tracker ─────────────────────────────────────────────────── */}
      {session && (
        <div className="flex items-center gap-1 px-6 py-2.5 border-b border-slate-800 bg-slate-900/50 shrink-0 overflow-x-auto">
          {PIPELINE_STAGES.map((stage, i) => {
            const isDone = stageIndex > i;
            const isCurrent = stageIndex === i;
            const isFuture = stageIndex < i && !isTerminal;
            return (
              <div key={stage.key} className="flex items-center gap-1 shrink-0">
                <div
                  className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
                    isCurrent
                      ? `${stateMeta.color} ${stateMeta.bg} border-current`
                      : isDone
                      ? "text-emerald-400 bg-emerald-950/30 border-emerald-800/50"
                      : "text-slate-600 bg-slate-900 border-slate-800"
                  }`}
                >
                  {isDone && <span className="mr-1">✓</span>}
                  {stage.label}
                </div>
                {i < PIPELINE_STAGES.length - 1 && (
                  <ChevronRight className={`w-3 h-3 shrink-0 ${isDone ? "text-emerald-700" : "text-slate-700"}`} />
                )}
              </div>
            );
          })}
          {isTerminal && !PIPELINE_STAGES.find((s) => s.key === currentState) && (
            <div className={`ml-2 px-3 py-1 rounded-full text-xs font-semibold border ${stateMeta.color} ${stateMeta.bg}`}>
              ⚠ {stateMeta.label}
            </div>
          )}
        </div>
      )}

      {/* ── Main Body ────────────────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── Left: Recent Sessions ──────────────────────────────────────────── */}
        <div className="w-56 border-r border-slate-800 bg-slate-900/40 flex flex-col shrink-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800 text-xs text-slate-500 uppercase tracking-widest font-semibold">
            Recent
          </div>
          <div className="flex-1 overflow-y-auto py-2">
            {recentSessions?.items.map((app) => {
              const meta = STATE_META[app.current_state] ?? FALLBACK_META;
              return (
                <button
                  key={app.id}
                  onClick={() => handleLoad(app.id)}
                  className={`w-full text-left px-4 py-3 border-b border-slate-800/50 hover:bg-slate-800/60 transition-colors ${
                    app.id === sessionId ? "bg-slate-800/80 border-l-2 border-l-sky-500" : ""
                  }`}
                >
                  <div className="text-xs font-mono text-slate-400 truncate">{app.id.slice(0, 14)}…</div>
                  <div className={`text-xs font-semibold mt-0.5 ${meta.color}`}>{meta.label}</div>
                  <div className="text-xs text-slate-600 mt-0.5">${app.loan_amount.toLocaleString()}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* ── Center: Actions ───────────────────────────────────────────────── */}
        <div className="flex flex-col flex-1 overflow-hidden">
          {!sessionId ? (
            <div className="flex-1 flex items-center justify-center text-slate-600">
              <div className="text-center">
                <Terminal className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <div className="text-sm">No session loaded.</div>
                <div className="text-xs mt-1">Create a new session or paste an ID above.</div>
              </div>
            </div>
          ) : isLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="w-6 h-6 animate-spin text-sky-500" />
            </div>
          ) : isError ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center text-red-400">
                <XCircle className="w-10 h-10 mx-auto mb-2" />
                <div className="text-sm">Session not found or access denied.</div>
              </div>
            </div>
          ) : (
            <>
              {/* Session Detail Card */}
              <div className="border-b border-slate-800 bg-slate-900/60 px-6 py-4 shrink-0">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg border ${stateMeta.bg}`}>
                      <StateIcon className={`w-4 h-4 ${stateMeta.color}`} />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-100">{stateMeta.label}</div>
                      <div className="flex items-center text-xs text-slate-500 font-mono mt-0.5">
                        {session?.id}
                        <CopyButton text={session?.id ?? ""} />
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-right">
                    <div>
                      <div className="text-xs text-slate-500">Loan</div>
                      <div className="text-sm font-semibold text-slate-200">${session?.loan_amount.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500">Term</div>
                      <div className="text-sm font-semibold text-slate-200">{session?.loan_term}mo</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500">Bureau</div>
                      <div className="text-sm font-semibold text-slate-200">{session?.bureau_gate_status ?? "—"}</div>
                    </div>
                  </div>
                </div>

                {/* Explanation strip if present */}
                {session?.explanation?.approved_terms && (
                  <div className="mt-2 p-3 bg-emerald-950/40 border border-emerald-800/50 rounded-lg text-xs">
                    <span className="text-emerald-400 font-semibold">Approved Terms: </span>
                    <span className="text-emerald-300">
                      ${session.explanation.approved_terms.final_loan_amount.toLocaleString()} over{" "}
                      {session.explanation.approved_terms.final_tenure_months} months · EMI ${session.explanation.approved_terms.monthly_emi.toLocaleString()}/mo
                    </span>
                  </div>
                )}
                {session?.explanation?.counter_offer && (
                  <div className="mt-2 p-3 bg-blue-950/40 border border-blue-800/50 rounded-lg text-xs">
                    <span className="text-blue-400 font-semibold">Counter-Offer: </span>
                    <span className="text-blue-300">
                      ${session.explanation.counter_offer.proposed_loan_amount.toLocaleString()} · {session.explanation.counter_offer.reason}
                    </span>
                  </div>
                )}
                {session?.explanation?.rejection_details && (
                  <div className="mt-2 p-3 bg-red-950/40 border border-red-800/50 rounded-lg text-xs">
                    <span className="text-red-400 font-semibold">Rejection: </span>
                    <span className="text-red-300">{session.explanation.rejection_details.reason}</span>
                  </div>
                )}
                {session?.explanation?.reprompt_requirements && (
                  <div className="mt-2 p-3 bg-orange-950/40 border border-orange-800/50 rounded-lg text-xs">
                    <span className="text-orange-400 font-semibold">Reprompt Required: </span>
                    <span className="text-orange-300">
                      {session.explanation.reprompt_requirements.missing_fields.join(", ")}
                    </span>
                  </div>
                )}
              </div>

              {/* Actions grid */}
              <div className="flex-1 overflow-y-auto p-4">
                {availableActions.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-slate-600">
                    <ShieldCheck className="w-10 h-10 mb-2 opacity-30" />
                    <div className="text-sm">
                      {isTerminal ? "Terminal state — no further transitions." : "No actions available for current state."}
                    </div>
                    <div className={`mt-2 text-xs ${stateMeta.color}`}>{currentState}</div>
                  </div>
                ) : (
                  <>
                    <div className="text-xs text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                      <Zap className="w-3 h-3 text-sky-500" />
                      Available Transitions ({availableActions.length})
                    </div>
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                      {availableActions.map((action) => (
                        <ActionPanel
                          key={action.id}
                          action={action}
                          sessionId={sessionId}
                          onSuccess={handleActionSuccess}
                          onError={handleActionError}
                        />
                      ))}
                    </div>
                  </>
                )}
              </div>
            </>
          )}
        </div>

        {/* ── Right: Activity Log ────────────────────────────────────────────── */}
        <div className="w-72 border-l border-slate-800 bg-slate-900/30 flex flex-col shrink-0 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
            <span className="text-xs text-slate-500 uppercase tracking-widest font-semibold">Activity Log</span>
            <button
              onClick={() => setLogs([mkLog("info", "Log cleared.")])}
              className="text-xs text-slate-600 hover:text-slate-400 transition-colors"
            >
              Clear
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-0.5">
            {logs.map((entry) => (
              <LogLine key={entry.id} entry={entry} />
            ))}
            <div ref={logEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
}
