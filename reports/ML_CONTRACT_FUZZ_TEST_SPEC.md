# ML Inference Contract Fuzz Test Specification

**Role:** Principal QA Engineer  
**Target Function:** `test_ml_contract_fuzzing()`  
**Objective:** Guarantee that the Pydantic API layer of the ML Inference Service acts as an impermeable shield, perfectly coercing or rejecting malformed JSON payloads *before* they can crash the deserialized `scikit-learn` matrix multiplication logic.

---

## Base Assumptions
The target endpoint is `POST /v1/predict` (internal to the ML Inference Service).
The expected feature schema for E3 is:
*   `cibil_score`: integer (300-900)
*   `net_monthly_income`: number (>0)
*   `age`: integer (18-100)
*   `time_with_curr_empr`: integer (>=0)
*   `education`: string (Enum strictly defined)

---

## 1. Valid Payload (The Golden Path)
*   **Description:** A perfectly formed JSON payload matching all expected types and constraints.
*   **Payload:**
    ```json
    {
      "cibil_score": 750,
      "net_monthly_income": 85000.50,
      "age": 35,
      "time_with_curr_empr": 48,
      "education": "GRADUATE"
    }
    ```
*   **Expected HTTP Status:** `200 OK`
*   **Expected Validation Response:** Successful model inference (e.g., `{"archetype": "Mid-Career Established"}`).
*   **Expected Audit Behavior:** Logs `E3_INFERENCE_SUCCESS` event with the exact payload and the resulting prediction.

---

## 2. Null Payloads
*   **Description:** Explicitly passing `null` for a required numerical field. ML models cannot perform math on `null` (unless an imputer is explicitly configured).
*   **Payload:**
    ```json
    {
      "cibil_score": 750,
      "net_monthly_income": null,
      "age": 35,
      "time_with_curr_empr": 48,
      "education": "GRADUATE"
    }
    ```
*   **Expected HTTP Status:** `422 Unprocessable Entity`
*   **Expected Validation Response:** `{"detail": [{"loc": ["body", "net_monthly_income"], "msg": "none is not an allowed value", "type": "type_error.none.not_allowed"}]}`
*   **Expected Audit Behavior:** Logs `E3_VALIDATION_FAILED`. The Orchestrator halts and logs an `ASSESSMENT_FAILED` event.

---

## 3. Missing Fields
*   **Description:** Entirely omitting a mandatory field from the JSON object.
*   **Payload:**
    ```json
    {
      "cibil_score": 750,
      "age": 35,
      "education": "GRADUATE"
    }
    ```
*   **Expected HTTP Status:** `422 Unprocessable Entity`
*   **Expected Validation Response:** `{"detail": [{"loc": ["body", "net_monthly_income"], "msg": "field required", "type": "value_error.missing"}, {"loc": ["body", "time_with_curr_empr"], "msg": "field required", "type": "value_error.missing"}]}`
*   **Expected Audit Behavior:** Logs `E3_VALIDATION_FAILED`.

---

## 4. Extra Fields (Schema Drift)
*   **Description:** The Orchestrator forwards a payload containing new fields the model wasn't trained on.
*   **Payload:**
    ```json
    {
      "cibil_score": 750,
      "net_monthly_income": 85000,
      "age": 35,
      "time_with_curr_empr": 48,
      "education": "GRADUATE",
      "number_of_dependents": 2,
      "favorite_color": "blue"
    }
    ```
*   **Expected HTTP Status:** `200 OK`
*   **Expected Validation Response:** The API must silently drop `number_of_dependents` and `favorite_color`, passing only the 5 expected features to the model. Returns successful prediction.
*   **Expected Audit Behavior:** Logs `E3_INFERENCE_SUCCESS`. The payload logged should ideally be the sanitized version actually passed to the model.

---

## 5. Wrong Datatypes (Stringified Numbers)
*   **Description:** A classic JSON integration error where numbers are passed as strings.
*   **Payload:**
    ```json
    {
      "cibil_score": "750",
      "net_monthly_income": "85000.50",
      "age": 35,
      "time_with_curr_empr": 48,
      "education": "GRADUATE"
    }
    ```
*   **Expected HTTP Status:** `200 OK`
*   **Expected Validation Response:** Pydantic must safely coerce `"750"` to integer `750` and `"85000.50"` to float `85000.50`. Returns successful prediction.
*   **Expected Audit Behavior:** Logs `E3_INFERENCE_SUCCESS` with the *coerced* payload to ensure mathematical reproducibility.

---

## 6. Boundary Values
*   **Description:** Testing the absolute edges of the logical constraints.
*   **Payload:**
    ```json
    {
      "cibil_score": 300,
      "net_monthly_income": 0.01,
      "age": 18,
      "time_with_curr_empr": 0,
      "education": "SSC"
    }
    ```
*   **Expected HTTP Status:** `200 OK`
*   **Expected Validation Response:** Successful model inference.
*   **Expected Audit Behavior:** Logs `E3_INFERENCE_SUCCESS`.

---

## 7. Unicode Strings (SQL Injection / XSS Attempts)
*   **Description:** Attempting to break the string parser or downstream database with unexpected unicode characters in an enum field.
*   **Payload:**
    ```json
    {
      "cibil_score": 750,
      "net_monthly_income": 85000,
      "age": 35,
      "time_with_curr_empr": 48,
      "education": "GRADUATE 🤖 DROP TABLE;"
    }
    ```
*   **Expected HTTP Status:** `422 Unprocessable Entity`
*   **Expected Validation Response:** `{"detail": [{"loc": ["body", "education"], "msg": "value is not a valid enumeration member", "type": "type_error.enum"}]}`
*   **Expected Audit Behavior:** Logs `E3_VALIDATION_FAILED`. The system must never execute the model on arbitrary strings.

---

## 8. Empty Strings
*   **Description:** Passing empty strings instead of nulls for categorical features.
*   **Payload:**
    ```json
    {
      "cibil_score": 750,
      "net_monthly_income": 85000,
      "age": 35,
      "time_with_curr_empr": 48,
      "education": ""
    }
    ```
*   **Expected HTTP Status:** `422 Unprocessable Entity`
*   **Expected Validation Response:** Fails the Enum validation check. 
*   **Expected Audit Behavior:** Logs `E3_VALIDATION_FAILED`.

---

## 9. Extremely Large Numbers (Overflow Protection)
*   **Description:** Sending numbers that exceed standard 32-bit or 64-bit bounds, attempting to trigger a Python `OverflowError` during scaling.
*   **Payload:**
    ```json
    {
      "cibil_score": 750,
      "net_monthly_income": 9e999,
      "age": 35,
      "time_with_curr_empr": 48,
      "education": "GRADUATE"
    }
    ```
*   **Expected HTTP Status:** `422 Unprocessable Entity` (or `400 Bad Request` if JSON parser fails).
*   **Expected Validation Response:** Must be caught by the JSON parser or a Pydantic `le` (less than or equal to) maximum constraint before reaching NumPy.
*   **Expected Audit Behavior:** Logs `E3_VALIDATION_FAILED`.

---

## 10. Negative Values
*   **Description:** Sending mathematically valid primitives that break business logic.
*   **Payload:**
    ```json
    {
      "cibil_score": 750,
      "net_monthly_income": -5000,
      "age": -5,
      "time_with_curr_empr": 48,
      "education": "GRADUATE"
    }
    ```
*   **Expected HTTP Status:** `422 Unprocessable Entity`
*   **Expected Validation Response:** Pydantic `gt` (greater than) constraints must catch this. `{"detail": [{"loc": ["body", "net_monthly_income"], "msg": "ensure this value is greater than 0"}]}`
*   **Expected Audit Behavior:** Logs `E3_VALIDATION_FAILED`.
