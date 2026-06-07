# RiskIntel ML Inference Service Validation Framework

**Role:** Principal MLOps Architect  
**Status:** Architecture Specification  

## Overview
With the retirement of E1, the ML Inference Service is now exclusively responsible for computing E3 (Borrower Archetype) and E4 (Credit Recommendations). Because this service sits at the critical juncture between the Orchestrator's raw JSON payloads and strictly-typed Python mathematical models, it represents the highest density of hidden integration risks in the backend architecture.

This document outlines the mandatory validation framework required to harden the ML Inference Service against data, schema, and serialization failures before production deployment.

---

## 1. Data Contract Risks

*   **Failure Scenario:** The frontend/Orchestrator sends an integer for `net_monthly_income` as a string (`"85000"` instead of `85000`). The Python JSON parser parses it as a string, but the serialized model expects a NumPy `float64`.
*   **Production Impact:** The model throws a `TypeError` during matrix multiplication, causing a 500 Internal Server Error, halting the entire Orchestrator DAG for that applicant.
*   **Detection Mechanism:** Pydantic validation layers at the FastAPI boundary.
*   **Automated Test:** `test_strict_type_coercion()` - Send payloads with deliberately mis-typed primitives (strings for ints, floats for ints) and assert that the API either safely coerces them or returns a 422 Unprocessable Entity before touching the model.
*   **Acceptance Criteria:** 100% of incoming requests are cast into strict Pydantic schemas that perfectly mirror the model's expected `dtype` before inference execution.

## 2. Serialization Risks

*   **Failure Scenario:** The E3 model was trained and pickled using `scikit-learn 1.4` on Python 3.10. The production Inference Service Docker image is built using `scikit-learn 1.5` on Python 3.12. The `pickle.load()` call fails silently or alters the internal centroid structures.
*   **Production Impact:** The service fails to boot, or worse, boots but assigns applicants to incorrect archetypes due to silent mathematical drift in the deserialized C-bindings.
*   **Detection Mechanism:** Container SHA-256 matching and dependency pinning.
*   **Automated Test:** `test_environment_parity()` - Extract the `requirements.txt` from the training artifact metadata and strictly compare it against the `pip freeze` of the inference container during the CI build.
*   **Acceptance Criteria:** The CI/CD pipeline immediately fails the build if the exact major/minor versions of `scikit-learn`, `numpy`, and `pandas` do not match between training and inference environments.

## 3. Scaler Mismatch Risks

*   **Failure Scenario:** The inference service correctly loads the E3 K-Means model but accidentally uses a `StandardScaler` fitted on a different dataset or uses raw, unscaled features for inference.
*   **Production Impact:** K-Means is extremely sensitive to scale. Applicants making $85,000 will be clustered based on income magnitude overriding all other features, resulting in 100% of applicants being assigned to a single, mathematically incorrect archetype.
*   **Detection Mechanism:** Pipeline serialization.
*   **Automated Test:** `test_golden_record_inference()` - Feed a "golden record" (a known applicant from the test set) through the API endpoint. Assert that the output cluster assignment and centroid distances perfectly match the training set output to 5 decimal places.
*   **Acceptance Criteria:** The model and the scaler must be exported and loaded as a single `sklearn.pipeline.Pipeline` object, guaranteeing the scaler can never decouple from the model.

## 4. Model Artifact Versioning Risks

*   **Failure Scenario:** A data scientist pushes a retrained E3 model to the S3 bucket (`e3_model_latest.pkl`), overwriting the previous version without updating the registry database.
*   **Production Impact:** The Inference Service silently re-downloads the new model on restart. The business loses all model lineage traceability, violating FCRA compliance for any adverse actions or bias investigations.
*   **Detection Mechanism:** Immutable artifact URIs and Registry checksums.
*   **Automated Test:** `test_artifact_immutability()` - Attempt to overwrite an existing model artifact in the testing S3 bucket. Ensure the system throws a permission error.
*   **Acceptance Criteria:** Model artifacts are immutable. The Inference Service must explicitly query the `model_registry` database for a specific version UUID and fail to boot if the downloaded file's SHA-256 hash does not match the registry hash.

## 5. Missing Value Risks

*   **Failure Scenario:** The frontend form makes `time_with_curr_empr` optional. An applicant submits the form, and the Orchestrator sends a `null` value. The model training pipeline dropped NaNs, so it has no imputation strategy.
*   **Production Impact:** The `predict()` method encounters a `NaN` and throws a `ValueError: Input contains NaN`, crashing the inference request.
*   **Detection Mechanism:** Upstream Orchestrator validation and Model-level imputation.
*   **Automated Test:** `test_missing_feature_handling()` - Send payloads missing one or multiple features. Assert that the service returns a graceful 400/422 error detailing the exact missing fields required for E3.
*   **Acceptance Criteria:** The ML Inference API contract strictly enforces required fields. The service must never reach the `predict()` method if mandatory features are missing.

## 6. Schema Drift Risks

*   **Failure Scenario:** The frontend adds a new feature (`dependents_count`) to the payload. The Orchestrator forwards this entire payload to the ML Inference Service.
*   **Production Impact:** The inference service passes an array of 5 features to a model expecting 4 features. `ValueError: X has 5 features, but KMeans is expecting 4 features as input.` 
*   **Detection Mechanism:** Strict feature masking.
*   **Automated Test:** `test_payload_overload()` - Send a payload with 10 extra, unmapped features. Assert that the inference service safely strips the unused features and successfully executes the model.
*   **Acceptance Criteria:** The Inference Service must act as a filter, explicitly extracting only the specific feature names ordered exactly as the model expects them, gracefully ignoring any additional JSON payload noise.

## 7. Backward Compatibility Risks

*   **Failure Scenario:** E3 version 2 is deployed. It renames the archetype labels (e.g., "Young Starters" becomes "Emerging Professionals"). The API returns this new string. The downstream Orchestrator logic, which triggers E4 limits based on the exact string "Young Starters", silently breaks.
*   **Production Impact:** Downstream rules fail to execute. Applicants receive $0 credit limits because their new archetype label is not recognized by the legacy rules.
*   **Detection Mechanism:** Consumer-Driven Contract (CDC) testing.
*   **Automated Test:** `test_api_contract_stability()` - Run the Orchestrator's parsing logic against the mocked response of the *new* ML Inference Service version during CI.
*   **Acceptance Criteria:** Model updates cannot arbitrarily change the shape or enum values of the API response. If an archetype label must change, the API must be versioned (e.g., `/v2/predict`), allowing the Orchestrator to migrate safely.
