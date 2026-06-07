# RiskIntel Frontend Release Candidate Audit Report

## Executive Summary: Live Demo Viability
**Verdict: NO.**

This frontend would **not** survive a live demo in front of judges.
1. **Critical Failure (P0):** A syntax error in the primary assessment form prevents the application from rendering the "Standard Credit Assessment" flow entirely.
2. **Robustness Issues (P1):** The application loses all state on browser refresh, and API error handling is fundamentally broken (form data is wiped if the backend returns a validation error).
3. **Logic Gaps (P1):** Major discrepancies between frontend validation and backend schema requirements lead to silent "API Error 400" failures that the user cannot recover from.

---

## P0: Critical Defects (Blockers)

### 1. Syntax Error in Traditional Assessment Form
*   **Severity:** P0
*   **Reproduction Steps:**
    1. Open the application.
    2. Click "Standard Credit Assessment".
    3. The application crashes/fails to render the form (in dev mode, Vite shows a Parse Error).
*   **Root Cause:** Missing key in `setFormData` object update. The code attempts to update state using `[ 'field', ... ].includes(name) ? ...` without assigning it to a key.
*   **Exact Files:** `frontend/src/components/forms/TraditionalAssessmentForm.jsx`
*   **Smallest Safe Fix:**
    ```javascript
    // Line 23
    [name]: ['annual_income', ...].includes(name) ? ...
    ```

---

## P1: High Severity Defects

### 2. Broken API Error Handling (Form State Loss)
*   **Severity:** P1
*   **Reproduction Steps:**
    1. Fill out any assessment form.
    2. Submit with data that triggers a backend validation error (e.g., Loan Term > 20).
    3. The form unmounts for "Processing...", then re-mounts empty with an "API Error: 400" message.
*   **Root Cause:** `App.jsx` unmounts the form component when `isLoading` is true. When the API fails, the form is re-mounted, losing all user input.
*   **Exact Files:** `frontend/src/App.jsx`
*   **Smallest Safe Fix:** Keep the form mounted but disabled/overlayed during `isLoading`, or move form state to the `App` component.

### 3. Missing Session Persistence
*   **Severity:** P1
*   **Reproduction Steps:**
    1. Complete an assessment to reach the results page.
    2. Refresh the browser.
    3. The application resets to the landing page; results are lost.
*   **Root Cause:** State is stored in memory (`useState`) and never synced to `localStorage`.
*   **Exact Files:** `frontend/src/App.jsx`
*   **Smallest Safe Fix:** Add `useEffect` hooks to persist `currentPersona` and `viewState` to `localStorage`.

### 4. Validation Mismatch (Frontend vs Backend)
*   **Severity:** P1
*   **Reproduction Steps:**
    1. Enter "24" in "Loan Term (Months)" on the Traditional form.
    2. Submit.
    3. Result: "API Error 400" because backend max is 20.
*   **Root Cause:** Frontend `max` attributes (e.g., 120) do not align with Pydantic schema limits (20) in `backend/app/schemas/requests.py`.
*   **Exact Files:** `frontend/src/components/forms/TraditionalAssessmentForm.jsx`, `frontend/src/components/forms/NTCAssessmentForm.jsx`
*   **Smallest Safe Fix:** Align `min`/`max` values in JSX with the backend `Field` constraints.

### 5. Broken Edit Flow for Re-routed NTCs
*   **Severity:** P1
*   **Reproduction Steps:**
    1. Start a "Standard Assessment" with CIBIL Score = 0.
    2. Submit (this re-routes to the NTC engine).
    3. On the results page, click "Edit Assessment".
    4. Result: The NTC form opens, but it is populated with (or missing) data from the Traditional form's schema.
*   **Root Cause:** `App.jsx` uses the *resulting* `user_type` to determine which form to show, but the *original* form used was different.
*   **Exact Files:** `frontend/src/App.jsx`
*   **Smallest Safe Fix:** Track the `originalViewState` in the persona object and return to that view on Edit.

---

## P2: Medium/Low Severity Defects

### 6. Missing Applicant Identity on Results
*   **Severity:** P2
*   **Reproduction Steps:** View any assessment result.
*   **Root Cause:** The borrower's name is not displayed anywhere on the results dashboard, making the report feel impersonal and "generic".
*   **Exact Files:** `frontend/src/App.jsx`, `frontend/src/components/OutcomeHero.jsx`
*   **Smallest Safe Fix:** Add `{currentPersona.applicant.full_name}` to the results header.

### 7. Impure Render Call (`Date.now()`)
*   **Severity:** P2
*   **Reproduction Steps:** Run `npm run lint`.
*   **Root Cause:** Calling `Date.now()` inside JSX leads to unstable Reference IDs that change on every re-render.
*   **Exact Files:** `frontend/src/App.jsx`
*   **Smallest Safe Fix:** Move the ID generation into a `useMemo` or a stable state.

### 8. Bloated Components (Unused Imports)
*   **Severity:** P2
*   **Reproduction Steps:** Run `npm run lint`.
*   **Root Cause:** Multiple components import unused icons (`Inbox`, `Target`) or `React` (unnecessary in modern React).
*   **Exact Files:** `App.jsx`, `LandingDashboard.jsx`, etc.
*   **Smallest Safe Fix:** Remove unused imports as identified by ESLint.
