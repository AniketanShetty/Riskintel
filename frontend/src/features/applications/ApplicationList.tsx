import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getApplications } from "@/api/applications";
import type { ApplicationListResponse } from "@/api/contracts";

export default function ApplicationList() {
  const [applications, setApplications] = useState<ApplicationListResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchApps() {
      try {
        const res = await getApplications(0, 50);
        setApplications(res.items);
      } catch (err: any) {
        setError("Failed to load applications.");
      } finally {
        setLoading(false);
      }
    }
    fetchApps();
  }, []);

  const getStateColor = (state: string) => {
    switch (state) {
      case "READY":
        return "bg-green-100 text-green-800 border-green-200";
      case "NEARLY_READY":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "NOT_READY_YET":
        return "bg-amber-100 text-amber-800 border-amber-200";
      case "REJECTED":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-slate-100 text-slate-800 border-slate-200";
    }
  };

  return (
    <div className="max-w-5xl mx-auto mt-6 bg-slate-50 border border-border rounded-xl p-8 shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold tracking-tight">Applications</h2>
        <Link to="/apply" className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90">
          New Application
        </Link>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-destructive/10 border-l-4 border-destructive text-destructive text-sm rounded-r-md">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-10 text-muted-foreground">Loading...</div>
      ) : applications.length === 0 ? (
        <div className="text-center py-10 text-muted-foreground bg-white rounded-lg border border-border">
          No applications found. Create one to get started.
        </div>
      ) : (
        <div className="overflow-x-auto bg-white rounded-lg border border-border">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-muted-foreground uppercase bg-slate-50 border-b border-border">
              <tr>
                <th className="px-6 py-3">Session ID</th>
                <th className="px-6 py-3">Applicant Name</th>
                <th className="px-6 py-3">Loan Amount</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((app) => (
                <tr key={app.id} className="border-b border-border last:border-0 hover:bg-slate-50">
                  <td className="px-6 py-4 font-mono text-xs truncate max-w-[150px]">{app.id}</td>
                  <td className="px-6 py-4 font-medium">Applicant</td>
                  <td className="px-6 py-4">${app.loan_amount.toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getStateColor(app.current_state)}`}>
                      {app.current_state}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link to={`/applications/${app.id}`} className="text-blue-600 hover:text-blue-800 hover:underline">
                      View Detail
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
