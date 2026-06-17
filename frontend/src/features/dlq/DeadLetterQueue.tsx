import { useEffect, useState } from "react";
import { getDeadLetters } from "@/api/applications";
import type { DeadLetterResponse } from "@/api/contracts";

export default function DeadLetterQueue() {
  const [items, setItems] = useState<DeadLetterResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetch() {
      try {
        const res = await getDeadLetters(0, 50);
        setItems(res.items);
        setTotal(res.total);
      } catch {
        setError("Failed to load dead letter queue.");
      } finally {
        setLoading(false);
      }
    }
    fetch();
  }, []);

  return (
    <div className="max-w-5xl mx-auto mt-6 bg-slate-50 border border-border rounded-xl p-8 shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Dead Letter Queue</h2>
          <p className="text-sm text-muted-foreground mt-1">Failed webhook events requiring manual review</p>
        </div>
        <span className="px-3 py-1 rounded-full bg-red-100 text-red-700 text-sm font-semibold border border-red-200">
          {loading ? "..." : total} events
        </span>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-destructive/10 border-l-4 border-destructive text-destructive text-sm rounded-r-md">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-10 text-muted-foreground">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-10 text-muted-foreground bg-white rounded-lg border border-border">
          No dead letter events. All webhooks processed successfully.
        </div>
      ) : (
        <div className="overflow-x-auto bg-white rounded-lg border border-border">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-muted-foreground uppercase bg-slate-50 border-b border-border">
              <tr>
                <th className="px-6 py-3">Session ID</th>
                <th className="px-6 py-3">Route</th>
                <th className="px-6 py-3">Failure Reason</th>
                <th className="px-6 py-3">Occurred At</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-border last:border-0 hover:bg-slate-50">
                  <td className="px-6 py-4 font-mono text-xs text-muted-foreground">
                    {item.session_id ?? "—"}
                  </td>
                  <td className="px-6 py-4 font-mono text-xs">{item.route}</td>
                  <td className="px-6 py-4 text-xs text-red-700">{item.failure_reason}</td>
                  <td className="px-6 py-4 text-xs text-muted-foreground">
                    {new Date(item.occurred_at).toLocaleString()}
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
