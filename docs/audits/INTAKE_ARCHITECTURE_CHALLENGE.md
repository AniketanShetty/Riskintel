# Intake Architecture Challenge
**Date:** 2026-06-11
**Auditor:** Independent Architecture Review Board

---

## 1. Challenging the Questionnaire Assumption
The traditional banking assumption is: *"We must gather all possible information upfront to make an accurate underwriting decision."* 

In microfinance, presenting a 20-field questionnaire to a farmer, gig worker, or homemaker causes massive cognitive overload. They may not know their exact "Annual Gross Income" or "Employer Address." Forcing everyone through a static form causes high drop-off rates and data hallucination (borrowers guessing answers just to get through the form).

---

## 2. Alternative Intake Architectures

### Architecture 1: Traditional Form Intake
A static, multi-page web form asking all demographic, financial, and employment questions upfront before any backend processing occurs.

*   **Completion Rate:** Low. Highly intimidating for farmers, homemakers, and gig workers.
*   **User Trust:** Medium. Feels like a standard bureaucratic bank.
*   **Explainability:** Perfect. The system has explicit inputs for every rule.
*   **Borrower Experience:** Poor. A gig worker is forced to leave "Employer Name" blank or enter "Self," causing frustration.
*   **Loan Officer Usefulness:** High. Generates a perfectly standardized PDF/dossier.
*   **Implementation Complexity:** Low. Basic CRUD forms.

### Architecture 2: Progressive Disclosure Intake (Just-In-Time Intake)
Starts with only PAN/Aadhaar (ID) and Loan Amount. The system instantly pings the bureau/backend. Based on the returned data, the system *only* asks questions needed to clear the specific missing rules. If the bureau proves excellent repayment history, it skips the behavioral questions. 

*   **Completion Rate:** High. Users only answer 3–5 highly contextual questions.
*   **User Trust:** High. Feels intelligent and respects the user's time.
*   **Explainability:** High.
*   **Borrower Experience:** Excellent. A farmer is only asked about crop cycles; a salaried user is only asked about employer stability.
*   **Loan Officer Usefulness:** High. The dossier highlights *why* a specific question was asked.
*   **Implementation Complexity:** High. Requires complex state machines and instant API integrations during the UX flow.

### Architecture 3: Conversational Intake (Voice / Chatbot)
A Whatsapp-style chatbot or voice assistant asks questions in natural language. ("Hi! How much do you need? What kind of work do you do?")

*   **Completion Rate:** Medium. Good for tech-illiterate users, but catastrophic if the NLP fails to parse an answer.
*   **User Trust:** Low. Users are highly suspicious of giving PAN numbers and income data to an AI chatbot.
*   **Explainability:** Low. The LLM might map "I drive an auto" to "Transportation Business" instead of "Gig Worker", creating hidden parsing errors.
*   **Borrower Experience:** Polarizing. Great if voice works natively; terrible if typing on a bad connection.
*   **Loan Officer Usefulness:** Medium. Unstructured chat logs are harder to audit than strict data fields.
*   **Implementation Complexity:** Extremely High. Requires robust LLM parsing, prompt injection defense, and state management.

---

## 3. Recommendation & Attack

**Recommendation:** I recommend **Architecture 2: Progressive Disclosure Intake**. It respects the borrower's time, handles the vast differences between a salaried worker and a homemaker natively, and preserves the strict, explainable data typing required by the Rule-Based Scorecard.

### Attacking My Own Recommendation

*The Committee's Critique of Progressive Disclosure:*

**Attack: The Thin-File Bait-and-Switch & Bureau Burn Rate**
Your Progressive Disclosure architecture relies on fetching a bureau report (CIBIL) immediately after asking for an ID and Loan Amount to "magically" skip questions. 
1.  **Bureau Cost Burn:** Pulling a CIBIL score costs money (e.g., ₹50). If you pull a bureau report *before* verifying if the user makes enough basic income to afford the loan, you are burning cash on thousands of obviously unqualified applicants.
2.  **The NTC Bait-and-Switch:** You listed Homemakers, Farmers, and New-To-Credit (NTC) borrowers as your target users. These demographics have "Thin Files" or no CIBIL score at all. When the backend ping fails to find them, your Progressive Disclosure system will panic and dynamically cascade into asking them *all 20 traditional questions anyway*. The "Progressive" UX becomes a bait-and-switch that is actually *more* frustrating than a static form because they have to hit "Next" 20 times instead of seeing everything on one page.

### Final Conclusion after Attack

The attack is brutally accurate. Relying on an immediate bureau ping to power the progressive disclosure will burn cash and fail spectacularly for NTC/Rural borrowers.

**Final Revised Architecture: Triage-Gated Progressive Disclosure**

We must implement a hybrid funnel.
1.  **Zero-Cost Triage Gate:** Ask exactly 3 zero-cost questions first: *Requested Amount, Primary Livelihood Source (Dropdown), and Estimated Monthly Income.*
2.  **Affordability Pre-Screen:** If the requested EMI completely crushes their declared income, reject immediately with coaching. Do not burn the ₹50 bureau fee.
3.  **Path Divergence:** 
    *   If they pass the pre-screen, *then* ping the bureau. 
    *   If they have a CIBIL score (Person A), progressively ask the 2-3 missing stability fields.
    *   If they are NTC/Thin File (Person B), gracefully route them into a **Gamified Readiness Assessment** rather than a punishing form, acknowledging upfront that we are building their profile from scratch.
