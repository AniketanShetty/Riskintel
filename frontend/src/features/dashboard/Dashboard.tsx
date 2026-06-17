import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getApplications } from "@/api/applications";
import { Activity, FileText, CheckCircle2, AlertCircle } from "lucide-react";

export default function Dashboard() {
  const [metrics, setMetrics] = useState({
    total: 0,
    ready: 0,
    nearlyReady: 0,
    notReadyYet: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchMetrics() {
      try {
        const res = await getApplications(0, 100);
        
        let ready = 0;
        let nearlyReady = 0;
        let notReadyYet = 0;

        res.items.forEach(app => {
          if (app.current_state === "READY") ready++;
          else if (app.current_state === "NEARLY_READY") nearlyReady++;
          else if (app.current_state === "NOT_READY_YET") notReadyYet++;
        });

        setMetrics({
          total: res.total, // Using server total since items might be paginated
          ready,
          nearlyReady,
          notReadyYet
        });
      } catch (err) {
        console.error("Failed to load metrics");
      } finally {
        setLoading(false);
      }
    }
    fetchMetrics();
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">Overview of loan application states</p>
        </div>
        <Link to="/apply" className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90">
          New Application
        </Link>
      </div>

      <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
        {/* Total Card */}
        <div className="rounded-xl border border-border bg-white p-6 shadow-sm flex flex-col gap-2">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Total Applications</h3>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="text-3xl font-bold">
            {loading ? "..." : metrics.total}
          </div>
        </div>

        {/* READY Card */}
        <div className="rounded-xl border border-border bg-white p-6 shadow-sm flex flex-col gap-2">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Ready</h3>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </div>
          <div className="text-3xl font-bold text-green-600">
            {loading ? "..." : metrics.ready}
          </div>
        </div>

        {/* NEARLY_READY Card */}
        <div className="rounded-xl border border-border bg-white p-6 shadow-sm flex flex-col gap-2">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Nearly Ready</h3>
            <Activity className="h-4 w-4 text-blue-500" />
          </div>
          <div className="text-3xl font-bold text-blue-600">
            {loading ? "..." : metrics.nearlyReady}
          </div>
        </div>

        {/* NOT_READY_YET Card */}
        <div className="rounded-xl border border-border bg-white p-6 shadow-sm flex flex-col gap-2">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Not Ready Yet</h3>
            <AlertCircle className="h-4 w-4 text-amber-500" />
          </div>
          <div className="text-3xl font-bold text-amber-600">
            {loading ? "..." : metrics.notReadyYet}
          </div>
        </div>
      </div>
    </div>
  );
}
