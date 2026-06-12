# Person B (New-To-Credit) Deterministic Framework
**Date:** 2026-06-11
**Auditor:** Independent Architecture Review Board

---

## 1. Initial Proposed Architecture (The "Alternative Data" Trap)

When banks attempt to underwrite New-to-Credit (NTC) borrowers, they typically build a scorecard based on proxy data.

*   **Score 1: Self-Reported Financial Health** (Declared Income vs Declared Expenses)
*   **Score 2: Alternative Data Footprint** (Post-paid telecom bills, utility bills)
*   **Score 3: Social/Peer Vouching** (Guarantors, local network strength)
*   **Score 4: Livelihood Quality** (Scoring "skilled" trades higher than "unskilled" gig work)

### The Attack (Bias, Gaming, and Risk)

*   **Attacking Score 1 (Financial Health):** Self-reported expenses are mathematically useless. Desperate borrowers will simply claim their expenses are ₹0 to pass the capacity check (gaming). 
*   **Attacking Score 2 (Alternative Data):** Massive regulatory and demographic bias. In rural India, utility bills and post-paid phones are almost exclusively in the name of the male head-of-household. A homemaker or female farmer will inherently score a zero here, creating a severe Disparate Impact violation (ECOA).
*   **Attacking Score 3 (Social Vouching):** Peer-liability models are prone to coercion (strong-arming peers into vouching). It also explicitly redlines migrant workers who have moved to a new city and have no local network.
*   **Attacking Score 4 (Livelihood Quality):** Subjective elitism. Punishing a Swiggy driver because their job is "unskilled" compared to a tailor is a domain failure. RiskIntel underwrites *cash flow*, not social status.

---

## 2. Redesigned Architecture (The Behavior & Action Framework)

We must abandon the attempt to approximate a CIBIL score using biased demographics. Instead, we underwrite **provable actions** and **standardized capacity**.

### Component 1: Implied Capacity Score
*   **Definition:** (Declared Income - Standardized Local Living Deduction) / Proposed EMI.
*   **Why it works:** By using a standardized, region-based deduction for living expenses (e.g., deducting ₹3,000 per dependent), we eliminate the borrower's ability to game their expense numbers. 
*   **Optimization Compatibility:** Perfect. If the score is too low, the engine lowers the `loan_amount` or extends the `tenure`.

### Component 2: Economic Consistency Score
*   **Definition:** Months continuously engaged in the current primary livelihood.
*   **Why it works:** We stop judging *what* the borrower does, and only judge *how long* they have done it. A gig worker doing deliveries for 2 years scores higher than a boutique owner of 2 months. 

### Component 3: Financial Discipline Proof
*   **Definition:** Binary check for any structured financial behavior (e.g., Active bank account, consistent digital wallet (UPI) usage, or participation in a local Self-Help Group / Chit fund).
*   **Why it works:** It replaces the biased "Utility Bill" requirement. Even unbanked farmers or homemakers often participate in local SHGs. It proves they understand structured cash management.
*   **Optimization Compatibility:** If a borrower fails this, the Optimization Engine can output a prerequisite condition: "Open a zero-balance Jan Dhan bank account to proceed."

### Component 4: Verification Strength
*   **Definition:** Can the borrower's identity and livelihood be verified physically or digitally?
*   **Override Rule:** This is the only score a Loan Officer can manually override. If digital verification fails, the officer can click "Field Verification Completed."

---

## 3. Verdict Boundaries & Optimization

The Optimization Engine mathematically searches for a configuration that passes the hard constraints of Implied Capacity and Verification.

### 🟢 READY
*   **Condition:** Passes all minimum thresholds on the original requested terms.
*   **Coaching Output:** "You are approved for your first builder loan. Making these payments on time will generate your first official CIBIL score, unlocking larger loans in the future."

### 🟡 NEARLY READY
*   **Condition:** Fails the Implied Capacity check on original terms, but the Optimization Engine successfully finds a path to approval.
*   **Coaching Output:** "Based on the standardized living costs for your area, a ₹50,000 loan creates an unsafe debt burden for you. However, we can approve you instantly for a ₹30,000 builder loan."
*   **Actionable Step:** Accept the optimized loan structure or add a co-borrower to increase Implied Capacity.

### 🔴 NOT READY YET
*   **Condition:** Extreme capacity failure (income does not cover standardized living costs, meaning any loan amount is unsafe), or total failure of Economic Consistency (started working yesterday).
*   **Coaching Output:** "You need a longer track record in your current livelihood before taking on formal debt. Return in 3 months with continuous work history, or join a local Self-Help Group to begin building your financial discipline proof."
