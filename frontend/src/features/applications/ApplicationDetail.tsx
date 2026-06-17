import { useParams } from "react-router-dom";
import { useApplication } from "@/hooks/useApplication";
import { FSMViewer } from "@/features/fsm/FSMViewer";
import { Button } from "@/components/ui/button";
import { Activity, AlertCircle, RefreshCw } from "lucide-react";

export const ApplicationDetailSkeleton = () => (
  <div className="flex h-[calc(100vh-4rem)] w-full overflow-hidden p-6 gap-6">
    <div className="flex-1 rounded-xl bg-slate-100 animate-pulse border border-border" />
    <div className="w-[400px] flex flex-col gap-6">
      <div className="h-64 rounded-xl bg-slate-100 animate-pulse border border-border" />
      <div className="h-48 rounded-xl bg-slate-100 animate-pulse border border-border" />
    </div>
  </div>
);

export const ApplicationErrorBoundary = ({ error, reset }: { error: Error; reset: () => void }) => (
  <div className="flex h-[calc(100vh-4rem)] items-center justify-center p-6">
    <div className="max-w-md w-full p-6 border-2 border-destructive/20 bg-destructive/5 rounded-xl flex flex-col items-center text-center gap-4">
      <AlertCircle className="w-10 h-10 text-destructive" />
      <h3 className="text-lg font-bold text-destructive">Failed to Load Pipeline</h3>
      <p className="text-sm text-destructive/80 mb-2">{error.message || "Application session not found or access denied."}</p>
      <Button onClick={reset} variant="destructive">
        <RefreshCw className="w-4 h-4 mr-2" /> Retry
      </Button>
    </div>
  </div>
);

export default function ApplicationDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: application, isLoading, isError, error, refetch } = useApplication(id!);

  if (isLoading) return <ApplicationDetailSkeleton />;
  if (isError || !application) return <ApplicationErrorBoundary error={error as Error} reset={refetch} />;

  return (
    <div className="flex h-[calc(100vh-4rem)] w-full overflow-hidden">
      {/* Left: React Flow DAG */}
      <div className="flex-1 p-6 pr-3">
        <FSMViewer application={application} />
      </div>

      {/* Right: Context Panel */}
      <div className="w-[400px] overflow-y-auto p-6 pl-3 border-l border-border bg-background">
        <div className="flex flex-col gap-6">
          
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 text-blue-600 rounded-lg"><Activity className="w-5 h-5" /></div>
            <div>
              <h2 className="text-lg font-bold tracking-tight">Session Pipeline</h2>
              <p className="text-xs font-mono text-muted-foreground">{application.id}</p>
            </div>
          </div>

          <div className="bg-slate-50 border border-border rounded-xl p-4">
            <h3 className="text-sm font-semibold mb-3">Application Metadata</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Status</span>
                <span className="font-semibold px-2 py-0.5 rounded-md bg-blue-100 text-blue-800 text-xs">{application.current_state}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Loan Amount</span>
                <span className="font-medium">${application.loan_amount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Purpose</span>
                <span className="font-medium capitalize">{application.loan_purpose.replace('_', ' ')}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Income Bracket</span>
                <span className="font-medium">{application.income_bracket}</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-50 border border-border rounded-xl p-4">
            <h3 className="text-sm font-semibold mb-3">Verification Telemetry</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Triage Pass</span>
                <span className="font-medium">{application.triage_pass === null ? "Pending" : application.triage_pass ? "Yes" : "No"}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Bureau Gate</span>
                <span className="font-medium">{application.bureau_gate_status || "Pending"}</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-50 border border-border rounded-xl p-4">
            <h3 className="text-sm font-semibold mb-3">Decision Explanation</h3>
            {application.explanation ? (
              <pre className="text-xs font-mono bg-slate-900 text-slate-50 p-3 rounded-lg overflow-x-auto">
                {JSON.stringify(application.explanation, null, 2)}
              </pre>
            ) : (
              <div className="text-sm text-muted-foreground italic">No explanation available yet.</div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
