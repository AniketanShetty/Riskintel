import React, { useState } from 'react';
import { ArrowRight, Loader2 } from 'lucide-react';

export default function NTCAssessmentForm({ onSubmit, isMentorMode, onCancel, initialData }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    full_name: initialData?.full_name || '',
    annual_income: initialData?.annual_income ?? 300000,
    monthly_expenses: initialData?.monthly_expenses ?? 15000,
    loan_amount: initialData?.loan_amount ?? 50000,
    loan_tenure: initialData?.loan_tenure ?? 12,
    primary_business: initialData?.primary_business || 'Retail Vendor',
    secondary_business: initialData?.secondary_business || 'None',
    young_dependents: initialData?.young_dependents ?? 1,
    old_dependents: initialData?.old_dependents ?? 0,
    occupants_count: initialData?.occupants_count ?? 2,
    home_ownership: initialData?.home_ownership ?? 0,
    type_of_house: initialData?.type_of_house || 'semi_pucca',
    sanitary_availability: initialData?.sanitary_availability ?? 1,
    water_availability: initialData?.water_availability || 'partial'
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ['annual_income', 'monthly_expenses', 'loan_amount', 'loan_tenure', 'young_dependents', 'old_dependents', 'occupants_count', 'home_ownership', 'sanitary_availability'].includes(name) 
        ? (value === '' ? '' : Number(value)) 
        : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    // Inject hidden defaults required by PersonBRequest
    const payload = {
      ...formData,
      user_type: "person_b",
      full_name: formData.full_name || "NTC Applicant",
      age: initialData?.age || 35,
      gender: initialData?.gender || "M",
      loan_purpose: initialData?.loan_purpose || "Business Expansion",
      loan_installments: formData.loan_tenure,
      social_class: initialData?.social_class || "N/A"
    };

    try {
      await onSubmit(payload, 'http://localhost:8000/api/assess/person-b');
    } catch (err) {
      setError(err.message || 'Assessment failed to process.');
      setLoading(false);
    }
  };

  const inputClass = `w-full p-3 rounded-xl border outline-none transition-colors ${
    isMentorMode 
      ? 'bg-slate-900 border-slate-700 text-slate-100 focus:border-emerald-500' 
      : 'bg-white border-slate-200 text-slate-900 focus:border-emerald-500'
  }`;

  const labelClass = `block text-sm font-medium mb-1 ${isMentorMode ? 'text-slate-300' : 'text-slate-700'}`;

  return (
    <div className={`max-w-2xl mx-auto rounded-3xl p-8 border shadow-sm ${isMentorMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200'} animate-fade-in`}>
      <div className="mb-8">
        <h2 className={`text-3xl font-bold mb-2 ${isMentorMode ? 'text-slate-100' : 'text-slate-900'}`}>Alternative Data Assessment</h2>
        <p className={isMentorMode ? 'text-slate-400' : 'text-slate-600'}>Evaluate a New-To-Credit borrower using livelihood and infrastructure proxies.</p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        
        {/* Section 1: Financials */}
        <div>
          <h3 className={`text-lg font-semibold mb-4 ${isMentorMode ? 'text-emerald-400' : 'text-emerald-700'}`}>1. Financials & Business</h3>
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
              <label className={labelClass}>Monthly Expenses (₹)</label>
              <input type="number" name="monthly_expenses" value={formData.monthly_expenses} onChange={handleChange} min="0" required className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Loan Amount (₹)</label>
              <input type="number" name="loan_amount" value={formData.loan_amount} onChange={handleChange} min="100" required className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Loan Tenure (Months)</label>
              <input type="number" name="loan_tenure" value={formData.loan_tenure} onChange={handleChange} min="1" required className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Primary Business</label>
              <input type="text" name="primary_business" value={formData.primary_business} onChange={handleChange} required className={inputClass} placeholder="e.g. Retail Vendor" />
            </div>
            <div>
              <label className={labelClass}>Secondary Business (Optional)</label>
              <input type="text" name="secondary_business" value={formData.secondary_business} onChange={handleChange} className={inputClass} />
            </div>
          </div>
        </div>

        {/* Section 2: Infrastructure */}
        <div>
          <h3 className={`text-lg font-semibold mb-4 pt-4 border-t ${isMentorMode ? 'text-emerald-400 border-slate-700' : 'text-emerald-700 border-slate-200'}`}>2. Infrastructure & Household</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className={labelClass}>House Type</label>
              <select name="type_of_house" value={formData.type_of_house} onChange={handleChange} className={inputClass}>
                <option value="pucca">Pucca (Concrete)</option>
                <option value="semi_pucca">Semi-Pucca</option>
                <option value="kucha">Kucha (Mud/Thatch)</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Home Ownership</label>
              <select name="home_ownership" value={formData.home_ownership} onChange={handleChange} className={inputClass}>
                <option value={1}>Owned</option>
                <option value={0}>Rented / Shared</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Sanitation Access</label>
              <select name="sanitary_availability" value={formData.sanitary_availability} onChange={handleChange} className={inputClass}>
                <option value={1}>Yes (Private/Shared Toilet)</option>
                <option value={0}>No (Public/None)</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Water Access</label>
              <select name="water_availability" value={formData.water_availability} onChange={handleChange} className={inputClass}>
                <option value="full">Full (Piped Indoors)</option>
                <option value="partial">Partial (Shared/Community)</option>
                <option value="none">None (Fetch required)</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Dependents (Young / Old)</label>
              <div className="flex gap-2">
                <input type="number" name="young_dependents" value={formData.young_dependents} onChange={handleChange} min="0" max="15" required className={inputClass} placeholder="Young" />
                <input type="number" name="old_dependents" value={formData.old_dependents} onChange={handleChange} min="0" max="10" required className={inputClass} placeholder="Old" />
              </div>
            </div>
            <div>
              <label className={labelClass}>Total Occupants</label>
              <input type="number" name="occupants_count" value={formData.occupants_count} onChange={handleChange} min="1" required className={inputClass} />
            </div>
          </div>
        </div>

        <div className="pt-6 flex justify-end gap-4 border-t border-slate-200/50">
          <button type="button" onClick={onCancel} className={`px-6 py-3 rounded-xl font-medium ${isMentorMode ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-800'}`}>
            Cancel
          </button>
          <button type="submit" disabled={loading} className="px-6 py-3 rounded-xl bg-emerald-600 text-white font-medium hover:bg-emerald-700 flex items-center gap-2 disabled:opacity-50">
            {loading ? <Loader2 size={20} className="animate-spin" /> : 'Run Assessment'}
            {!loading && <ArrowRight size={20} />}
          </button>
        </div>
      </form>
    </div>
  );
}
