import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createApplication } from "@/api/applications";
import { Button } from "@/components/ui/button";

export default function ApplyForm() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const formData = new FormData(e.currentTarget);
    
    try {
      const payload = {
        loan_amount: Number(formData.get("loan_amount")),
        loan_term: Number(formData.get("loan_term")),
        loan_purpose: formData.get("loan_purpose"),
        income_bracket: formData.get("income_bracket"),
        full_name: formData.get("full_name"),
        national_id: formData.get("national_id"),
        pincode: formData.get("pincode"),
      };
      
      const res = await createApplication(payload);
      navigate(`/applications/${res.session_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to submit application");
      setLoading(false);
    }
  };

  const inputClass = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50";

  return (
    <div className="max-w-2xl mx-auto mt-6 bg-slate-50 border border-border rounded-xl p-8 shadow-sm">
      <h2 className="text-2xl font-bold mb-6 tracking-tight">Loan Application Intake</h2>
      
      {error && (
        <div className="mb-6 p-4 bg-destructive/10 border-l-4 border-destructive text-destructive text-sm rounded-r-md">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-medium leading-none">Full Name</label>
            <input name="full_name" required className={inputClass} placeholder="Jane Doe" defaultValue="Demo User" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium leading-none">National ID</label>
            <input name="national_id" required className={inputClass} placeholder="SSN or ID" defaultValue="999-00-1234" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-medium leading-none">Loan Amount ($)</label>
            <input name="loan_amount" type="number" min="1000" max="500000" required className={inputClass} placeholder="50000" defaultValue={50000} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium leading-none">Loan Term (Months)</label>
            <select name="loan_term" required className={inputClass} defaultValue={12}>
              <option value="12">12 Months</option>
              <option value="24">24 Months</option>
              <option value="36">36 Months</option>
              <option value="48">48 Months</option>
              <option value="60">60 Months</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-medium leading-none">Loan Purpose</label>
            <select name="loan_purpose" required className={inputClass} defaultValue="medical">
              <option value="education">Education</option>
              <option value="medical">Medical</option>
              <option value="home_renovation">Home Renovation</option>
              <option value="wedding">Wedding</option>
              <option value="working_capital">Working Capital</option>
              <option value="debt_consolidation">Debt Consolidation</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium leading-none">Income Bracket</label>
            <select name="income_bracket" required className={inputClass} defaultValue="50k+">
              <option value="0-10k">0 - $10,000</option>
              <option value="10k-20k">$10,000 - $20,000</option>
              <option value="20k-30k">$20,000 - $30,000</option>
              <option value="30k-40k">$30,000 - $40,000</option>
              <option value="40k-50k">$40,000 - $50,000</option>
              <option value="50k+">$50,000+</option>
            </select>
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium leading-none">Pincode / ZIP</label>
          <input name="pincode" required className={inputClass} placeholder="12345" defaultValue="94105" />
        </div>

        <Button type="submit" disabled={loading} className="w-full">
          {loading ? "Submitting Application..." : "Submit Application"}
        </Button>
      </form>
    </div>
  );
}
