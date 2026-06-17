# ADR-028: Identity Verification String Matching Standards

**Date:** 2026-06-13
**Status:** PROPOSED
**Resolves:** Blockers identified in Phase 2 Audit concerning undefined fuzzy matching algorithms for identity verification.

---

## 1. Context & Repository Evidence

The RiskIntel V2 Constitution demands strict deterministic algorithms to eliminate bias. However, the repository audit revealed a significant specification gap regarding Identity Verification math:
*   `docs/output_specs/SCORECARD_FORMULAS.md` states: `national_id_match_score >= 0.85 (Fuzzy match of Name to PAN DB)`.
*   `models/applicant.py` contains the column: `national_id_match_score: Mapped[float] = mapped_column(Float, nullable=True)`.
*   Searches for `PAN matching`, `KYC matching`, and algorithmic standards (e.g., `Levenshtein`, `Jaro`) yielded **0 results**. 

Engineers implementing this logic without an explicitly defined algorithm would introduce non-deterministic third-party libraries, leading to unpredictable compliance failures across different environments.

---

## 2. Alternatives Analysis

We must select an algorithm to match the user-input `full_name` against the external PAN/Aadhaar database `kyc_name`.

### Option A: Standard Levenshtein Distance (Edit Distance)
*   **Mechanism:** Counts minimum single-character edits (insertions, deletions, substitutions).
*   **Pros:** Mathematically simple, widely understood.
*   **Cons:** Fails catastrophically on transposed names. In India, "Amit Kumar" on Aadhaar is frequently written as "Kumar Amit" on PAN. Levenshtein scores this as a massive failure distance, causing unacceptable false-negative rejections.

### Option B: Jaro-Winkler Distance
*   **Mechanism:** Measures edit distance but heavily boosts the score if the strings share a common prefix.
*   **Pros:** Excellent for minor typos in the first name.
*   **Cons:** Inherits the transposition weakness of Levenshtein. "Amit Kumar" vs "Kumar Amit" still fails because the prefixes do not match.

### Option C: Token Set Ratio Matching (Intersection over Union)
*   **Mechanism:** Tokenizes both strings by whitespace, sorts the tokens alphabetically, and calculates the similarity of the intersecting set against the remainders.
*   **Pros:** Perfectly handles transposed names ("Kumar Amit" == "Amit Kumar" returns 100%). Handles partial initials well. 
*   **Cons:** Slightly more complex to compute than pure Levenshtein.

---

## 3. Decision & Final Recommendation

We will implement **Option C: Token Set Ratio Matching**. 

Given the prevalence of surname/given-name transpositions in Indian KYC documents, pure Levenshtein creates an artificial barrier to entry (violating the Constitution's mandate to optimize for truth, not friction). Token Set Ratio provides the highest resilience to structural KYC variance while remaining mathematically deterministic.

To maintain a **low dependency footprint** and absolute environment determinism, we will rely on the standard `thefuzz` library (which implements Token Set Ratio) or implement a pure-Python set intersection of Levenshtein-scored tokens, completely avoiding unstable C-compiled native binaries.

---

## 4. Normalization Rules

Before the algorithm evaluates the two strings, they must mathematically pass through a strict, deterministic normalization pipeline:
1.  **Case Folding:** Convert entirely to lowercase.
2.  **Special Character Stripping:** Regex remove `[^a-z0-9\s]`. (e.g., "Dr.", "Mrs.", periods, hyphens, and commas are destroyed).
3.  **Whitespace Collapse:** Replace multiple spaces with a single space, and strip leading/trailing spaces.

---

## 5. Threshold Definition

The required passage threshold is strictly bounded: **`national_id_match_score >= 85.0`** (on a 0-100 scale).

---

## 6. Deterministic Test Vectors (Pytest Acceptance Criteria)

Engineers must implement these exact edge cases in CI to prove the matching algorithm is functioning deterministically:

| Scenario | Input `full_name` | DB `kyc_name` | Expected Match | Expected Score | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Exact Match** | "Rahul Sharma" | "Rahul Sharma" | PASS | `100.0` | Perfect string. |
| **Case & Symbol** | "Dr. Rahul-Sharma" | "rahul sharma" | PASS | `100.0` | Normalization strips "dr", ".", "-". |
| **Transposition** | "Sharma Rahul" | "Rahul Sharma" | PASS | `100.0` | Token Set Ratio perfectly aligns transposed words. |
| **Middle Name Drop**| "Rahul Kumar Sharma"| "Rahul Sharma" | PASS | `>= 85.0` | High intersection set overlap. |
| **Minor Typo** | "Rahul Sarma" | "Rahul Sharma" | PASS | `>= 85.0` | 1-character edit distance on token. |
| **Complete Mismatch**| "Rahul Sharma" | "Amit Patel" | FAIL | `< 50.0` | Zero intersection. |

---

## 7. Edge Cases

*   **Single-Word Names:** Common in rural India (e.g., "Rahul"). The algorithm processes single tokens gracefully, leaning heavily on exact character matching.
*   **Zero-Length Strings:** If normalization reduces either string to `""`, the system instantly fails the verification (`score = 0.0`) and transitions the state to `FRAUD_DETECTED` (Identity spoofing attempt).
