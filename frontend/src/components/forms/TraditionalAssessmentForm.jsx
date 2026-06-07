import React, { useState } from 'react';
import { ArrowRight, Loader2 } from 'lucide-react';

export default function TraditionalAssessmentForm({ onSubmit, isMentorMode, onCancel, initialData }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    full_name: initialData?.full_name || '',
    annual_income: initialData?.annual_income ?? 600000,
    loan_amount: initialData?.loan_amount ?? 150000,
    loan_term: initialData?.loan_term ?? 20,
    cibil_score: initialData?.cibil_score ?? 750,
    education: initialData?.education || 'Graduate',
    self_employed: initialData?.self_employed || 'No',
    dependents: initialData?.dependents ?? 1,
    bank_asset_value: initialData?.bank_asset_value ?? 0
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ['annual_income', 'loan_amount', 'loan_term', 'cibil_score', 'dependents', 'bank_asset_value'].includes(name)
        ? (value === '' ? '' : Number(value)) 
        : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    // Inject hidden defaults required by PersonARequest
    const payload = {
      ...formData,
      user_type: "person_a",
      full_name: formData.full_name || "Applicant",
      age: initialData?.age || 30,
      gender: initialData?.gender || "M",
      marital_status: initialData?.marital_status || "Single",
      years_at_current_employer: initialData?.years_at_current_employer || 1,
      loan_purpose: initialData?.loan_purpose || "personal",
      residential_assets_value: initialData?.residential_assets_value || 0,
      commercial_assets_value: initialData?.commercial_assets_value || 0,
      luxury_assets_value: initialData?.luxury_assets_value || 0
    };

    try {
      await onSubmit(payload, 'http://localhost:8000/api/assess/person-a');
    } catch (err) {
      setError(err.message || 'Assessment failed to process.');
      setLoading(false);
    }
  };

  const inputClass = `w-full p-3 rounded-xl border outline-none transition-colors ${
    isMentorMode 
      ? 'bg-slate-900 border-slate-700 text-slate-100 focus:border-blue-500' 
      : 'bg-white border-slate-200 text-slate-900 focus:border-blue-500'
  }`;

  const labelClass = `block text-sm font-medium mb-1 ${isMentorMode ? 'text-slate-300' : 'text-slate-700'}`;

  return (
    <div className={`max-w-2xl mx-auto rounded-3xl p-8 border shadow-sm ${isMentorMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'} animate-fade-in`}>
      <div className="mb-8">
        <h2 className={`text-3xl font-bold mb-2 ${isMentorMode ? 'text-slate-100' : 'text-slate-900'}`}>Standard Assessment</h2>
        <p className={isMentorMode ? 'text-slate-400' : 'text-slate-600'}>Evaluate an established borrower using traditional financial metrics.</p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label className={labelClass}>Full Name</label>
            <input type="text" name="full_name" value={formData.full_name} onChange={handleChange} required className={inputClass} placeholder="Enter your full name" />
          </div>
          <div>
            <label className={labelClass}>Annual Income (₹)</label>
            <input type="number" name="annual_income" value={formData.annual_income} onChange={handleChange} min="0" required className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>CIBIL Score</label>
            <input type="number" name="cibil_score" value={formData.cibil_score} onChange={handleChange} min="0" max="900" required className={inputClass} />
            <p className="text-xs text-slate-400 mt-1">Enter 0 to simulate New-To-Credit re-routing.</p>
          </div>
          
          <div>
            <label className={labelClass}>Loan Amount (₹)</label>
            <input type="number" name="loan_amount" value={formData.loan_amount} onChange={handleChange} min="1" required className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Loan Term (Months)</label>
            <input type="number" name="loan_term" value={formData.loan_term} onChange={handleChange} min="2" max="20" required className={inputClass} />
          </div>

          <div>
            <label className={labelClass}>Education</label>
            <select name="education" value={formData.education} onChange={handleChange} className={inputClass}>
              <option value="Graduate">Graduate</option>
              <option value="Not Graduate">Not Graduate</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>Self Employed?</label>
            <select name="self_employed" value={formData.self_employed} onChange={handleChange} className={inputClass}>
              <option value="Yes">Yes</option>
              <option value="No">No</option>
            </select>
          </div>
          
          <div>
            <label className={labelClass}>Dependents</label>
            <input type="number" name="dependents" value={formData.dependents} onChange={handleChange} min="0" max="5" required className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Total Declared Assets (₹)</label>
            <input type="number" name="bank_asset_value" value={formData.bank_asset_value} onChange={handleChange} min="0" required className={inputClass} placeholder="Total assets value" />
          </div>
        </div>

        <div className="pt-6 flex justify-end gap-4 border-t border-slate-200/50">
          <button type="button" onClick={onCancel} className={`px-6 py-3 rounded-xl font-medium ${isMentorMode ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-800'}`}>
            Cancel
          </button>
          <button type="submit" disabled={loading} className="px-6 py-3 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 flex items-center gap-2 disabled:opacity-50">
            {loading ? <Loader2 size={20} className="animate-spin" /> : 'Run Assessment'}
            {!loading && <ArrowRight size={20} />}
          </button>
        </div>
      </form>
    </div>
  );
}
