import math
import pandas as pd
from typing import Dict, Any, List

class ReadinessEngine:
    """Readiness Engine (E5) for New-To-Credit (NTC) borrowers."""

    def __init__(self):
        pass


    def _map_business_macro(self, biz: Any) -> str:
        """Map raw business text to macro category."""
        if pd.isna(biz) or biz is None:
            return "Services"
        biz_str = str(biz).strip().lower()
        if any(w in biz_str for w in ['farm', 'rear', 'dairy', 'goat', 'cow', 'agri']):
            return 'Agriculture'
        elif any(w in biz_str for w in ['tailor', 'grocer', 'vendor', 'shop', 'retail']):
            return 'Retail'
        elif any(w in biz_str for w in ['loom', 'handicraft', 'manufact', 'produc', 'weaver']):
            return 'Production'
        else:
            return 'Services'

    def _map_purpose_macro(self, purpose: Any) -> str:
        """Map raw loan purpose text to macro category."""
        if pd.isna(purpose) or purpose is None:
            return "Personal"
        pur_str = str(purpose).strip().lower()
        if any(w in pur_str for w in ['crop', 'livestock', 'agro', 'anim']):
            return 'Agriculture'
        elif any(w in pur_str for w in ['house', 'construct', 'repair']):
            return 'Housing'
        elif any(w in pur_str for w in ['work', 'capit', 'equip', 'raw', 'business']):
            return 'Business'
        else:
            return 'Personal'

    def _determine_status(self, score: float) -> str:
        """Determine component status label."""
        rounded_score = round(score)
        if rounded_score >= 70:
            return "Strong"
        elif rounded_score >= 50:
            return "Satisfactory"
        else:
            return "Needs Attention"

    # ── Policy thresholds (SSOT) ────────────────────────────────────────────
    # Module-level constants are the single source of truth for any code
    # that needs to reference these cutoffs (e.g. recommendation rules).
    # The engine itself and any downstream consumer MUST read from these
    # names rather than hardcoding the values.
    STRONG_STATUS_MIN = 70         # _determine_status "Strong" cutoff
    SATISFACTORY_STATUS_MIN = 50   # _determine_status "Satisfactory" cutoff
    BAND_READY_MIN = 75            # final band "Ready"
    BAND_MODERATELY_READY_MIN = 50 # final band "Moderately Ready"
    BAND_NEEDS_IMPROVEMENT_MIN = 25  # final band "Needs Improvement"

    def calculate_readiness(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate readiness score and band based on E5 specification.
        """
        imputed_fields: List[str] = []

        # ── 1. Clean and Extract Inputs ───────────────────────────────────────
        annual_income_raw = features.get('annual_income')
        monthly_expenses_raw = features.get('monthly_expenses')
        loan_amount_raw = features.get('loan_amount')
        
        home_ownership_raw = features.get('home_ownership')
        type_of_house_raw = features.get('type_of_house')
        house_area_raw = features.get('house_area')

        sanitary_availability_raw = features.get('sanitary_availability')
        water_availability_raw = features.get('water_availability')

        young_dependents_raw = features.get('young_dependents')
        old_dependents_raw = features.get('old_dependents')
        occupants_count_raw = features.get('occupants_count')

        primary_business_raw = features.get('primary_business')
        secondary_business_raw = features.get('secondary_business')
        loan_purpose_raw = features.get('loan_purpose')

        # Validate raw numeric inputs for NaN and Infinity if they are provided (not None)
        for name in [
            'annual_income', 'monthly_expenses', 'loan_amount', 'house_area',
            'sanitary_availability', 'water_availability', 'young_dependents',
            'old_dependents', 'occupants_count'
        ]:
            val = features.get(name)
            if val is not None:
                # Guard pd.isna against non-scalar types (list/array) which return an
                # array from pd.isna whose boolean evaluation raises a NumPy ValueError.
                if isinstance(val, (bool, int, float, str)) and pd.isna(val):
                    raise ValueError(f"{name} cannot be NaN.")
                try:
                    f_val = float(val)
                except (ValueError, TypeError):
                    continue
                if math.isnan(f_val):
                    raise ValueError(f"{name} cannot be NaN.")
                if math.isinf(f_val):
                    raise ValueError(f"{name} cannot be Infinity.")

        # ── 2. Imputation and Defaulting ──────────────────────────────────────
        if house_area_raw is None or pd.isna(house_area_raw):
            house_area = 450.0
            imputed_fields.append("house_area")
        else:
            try:
                house_area = float(house_area_raw)
            except (ValueError, TypeError):
                raise ValueError("house_area must be a valid number.")

        if secondary_business_raw is None or pd.isna(secondary_business_raw) or str(secondary_business_raw).strip().lower() in ['none', 'nan', '']:
            secondary_business_val = "none"
            if secondary_business_raw is None or pd.isna(secondary_business_raw):
                imputed_fields.append("secondary_business")
        else:
            secondary_business_val = str(secondary_business_raw).strip()

        # ── 3. Strict Input Range Validations ─────────────────────────────────
        try:
            annual_income = float(annual_income_raw) if annual_income_raw is not None else 0.0
            monthly_expenses = float(monthly_expenses_raw) if monthly_expenses_raw is not None else 0.0
            loan_amount = float(loan_amount_raw) if loan_amount_raw is not None else 0.0
        except (ValueError, TypeError):
            raise ValueError("annual_income, monthly_expenses, and loan_amount must be valid numbers.")

        if annual_income < 0:
            raise ValueError("Annual income cannot be negative.")
        if monthly_expenses < 0:
            raise ValueError("Monthly expenses cannot be negative.")
        if loan_amount < 0:
            raise ValueError("Loan amount cannot be negative.")
        if house_area < 0:
            raise ValueError("House area cannot be negative.")

        # Dependents and Occupants Validation
        try:
            young_dependents = int(young_dependents_raw) if young_dependents_raw is not None else 0
            old_dependents = int(old_dependents_raw) if old_dependents_raw is not None else 0
            occupants_count = int(occupants_count_raw) if occupants_count_raw is not None else 1
        except (ValueError, TypeError):
            raise ValueError("young_dependents, old_dependents, and occupants_count must be integers.")

        if young_dependents < 0:
            raise ValueError("young_dependents cannot be negative.")
        if old_dependents < 0:
            raise ValueError("old_dependents cannot be negative.")
        if occupants_count < 1:
            raise ValueError("occupants_count must be at least 1.")

        # Cross-field logical validation
        min_occupants = young_dependents + old_dependents + 1
        if occupants_count < min_occupants:
            raise ValueError(
                f"Total occupants count ({occupants_count}) must be at least the number of "
                f"dependents ({young_dependents + old_dependents}) plus the primary applicant."
            )

        # Infrastructure Access Validation & Translation
        if water_availability_raw is not None:
            if isinstance(water_availability_raw, str):
                water_val_str = water_availability_raw.strip().lower()
                if water_val_str == "none":
                    water_avail = 0.0
                elif water_val_str == "partial":
                    water_avail = 0.5
                elif water_val_str == "full":
                    water_avail = 1.0
                else:
                    try:
                        water_avail = float(water_availability_raw)
                    except ValueError:
                        raise ValueError(f"Invalid water_availability value: {water_availability_raw}")
            else:
                try:
                    water_avail = float(water_availability_raw)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid water_availability value: {water_availability_raw}")
        else:
            water_avail = 0.0

        if water_avail not in {0.0, 0.5, 1.0}:
            raise ValueError(f"water_availability must be one of [0, 0.5, 1]. Got {water_availability_raw}")

        if sanitary_availability_raw is not None:
            try:
                sanitary_avail = float(sanitary_availability_raw)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid sanitary_availability value: {sanitary_availability_raw}")
        else:
            sanitary_avail = 0.0

        if sanitary_avail not in {0.0, 1.0}:
            raise ValueError(f"sanitary_availability must be one of [0, 1]. Got {sanitary_availability_raw}")

        # ── 4. Translations ───────────────────────────────────────────────────
        # Home Ownership Calibration Translation and Validation
        home_ownership_str = str(home_ownership_raw).strip().lower() if home_ownership_raw is not None else "rented"
        if home_ownership_str in ['1', '1.0', 'owned']:
            home_ownership_internal = 'owned'
        elif home_ownership_str in ['0', '0.0', 'rented']:
            home_ownership_internal = 'rented'
        else:
            home_ownership_internal = home_ownership_str

        allowed_home_ownerships = {'owned', 'family_shared', 'rented', 'employer_provided'}
        if home_ownership_internal not in allowed_home_ownerships:
            raise ValueError(f"Invalid home_ownership value: {home_ownership_raw}")

        # House Type Translation and Validation
        house_type_str = str(type_of_house_raw).strip().lower() if type_of_house_raw is not None else "r"
        allowed_house_types = {'pucca', 'semi_pucca', 'kucha', 't1', 't2', 'r'}
        if house_type_str not in allowed_house_types:
            raise ValueError(f"Invalid type_of_house value: {type_of_house_raw}")

        if house_type_str in ['pucca', 't1']:
            house_type_internal = 'T1'
        elif house_type_str in ['semi_pucca', 't2']:
            house_type_internal = 'T2'
        else:
            house_type_internal = 'R'

        # ── 5. Component Score Calculations (Float Internally) ────────────────
        
        # 5.1 Financial Health (35%)
        # Guarded division parameters
        income_expense_ratio = annual_income / (max(1.0, monthly_expenses) * 12.0)
        # Do not clamp the denominator: using max(1.0, annual_income) inflates the
        # debt burden score when annual_income < 1.0.  The annual_income <= 0 floor
        # override below makes the ratio value irrelevant for that boundary.
        loan_income_ratio = loan_amount / annual_income if annual_income > 0 else float('inf')

        # Stability Ratio
        if income_expense_ratio < 1.0:
            stability_ratio_score = 0.0
        elif income_expense_ratio <= 3.0:
            stability_ratio_score = 50.0 * (income_expense_ratio - 1.0)
        else:
            stability_ratio_score = 100.0

        # Debt Burden Ratio
        if loan_income_ratio > 1.5:
            debt_burden_ratio_score = 0.0
        else:
            debt_burden_ratio_score = 100.0 * (1.5 - loan_income_ratio) / 1.5

        financial_health_score = 0.5 * stability_ratio_score + 0.5 * debt_burden_ratio_score
        financial_health_score = max(0.0, min(100.0, financial_health_score))

        if annual_income <= 0.0:
            financial_health_score = 0.0

        # 5.2 Housing Stability (20%)
        # Home Ownership
        if home_ownership_internal == 'owned':
            ownership_points = 40.0
        elif home_ownership_internal == 'family_shared':
            ownership_points = 30.0
        elif home_ownership_internal == 'rented':
            ownership_points = 20.0
        else:
            ownership_points = 10.0

        # House Type
        if house_type_internal == 'T1':
            house_type_points = 40.0
        elif house_type_internal == 'T2':
            house_type_points = 20.0
        else:
            house_type_points = 0.0

        # Dwelling Quality Interaction
        if house_type_internal == 'R':
            dwelling_quality_points = 0.0
        else:
            if house_area < 150.0:
                dwelling_quality_points = 5.0
            elif house_area <= 600.0:
                dwelling_quality_points = 15.0
            else:
                dwelling_quality_points = 20.0

        housing_stability_score = ownership_points + house_type_points + dwelling_quality_points
        housing_stability_score = max(0.0, min(100.0, housing_stability_score))

        # 5.3 Infrastructure Access (15%)
        sanitary_points = sanitary_avail * 50.0
        water_points = water_avail * 50.0
        infrastructure_access_score = sanitary_points + water_points
        infrastructure_access_score = max(0.0, min(100.0, infrastructure_access_score))

        # 5.4 Household Burden (15%)
        base_burden_score = 100.0
        young_dep_deduction = young_dependents * 10.0
        old_dep_deduction = old_dependents * 15.0
        occupants_deduction = max(0.0, occupants_count - 4) * 5.0

        household_burden_score = base_burden_score - (young_dep_deduction + old_dep_deduction + occupants_deduction)
        household_burden_score = max(0.0, min(100.0, household_burden_score))

        # 5.5 Business Viability (15%)
        # Runtime Category Mappings
        primary_business_macro = self._map_business_macro(primary_business_raw)
        loan_purpose_macro = self._map_purpose_macro(loan_purpose_raw)

        # Business Stability Base
        if primary_business_macro == 'Retail':
            biz_stability_points = 60.0
        elif primary_business_macro == 'Production':
            biz_stability_points = 50.0
        elif primary_business_macro == 'Agriculture':
            biz_stability_points = 40.0
        elif primary_business_macro == 'Services':
            biz_stability_points = 30.0
        else:
            biz_stability_points = 20.0

        # Intent Alignment Matrix
        # Aligned Rules
        is_aligned = (
            (primary_business_macro == 'Agriculture' and loan_purpose_macro == 'Agriculture') or
            (primary_business_macro == 'Retail' and loan_purpose_macro == 'Business') or
            (primary_business_macro == 'Production' and loan_purpose_macro == 'Business')
        )
        
        # Misaligned Rules
        is_misaligned = (
            (primary_business_macro == 'Agriculture' and loan_purpose_macro == 'Business') or
            (primary_business_macro == 'Retail' and loan_purpose_macro == 'Agriculture') or
            (primary_business_macro == 'Production' and loan_purpose_macro == 'Agriculture') or
            (primary_business_macro == 'Services' and loan_purpose_macro == 'Agriculture')
        )

        if is_aligned:
            alignment_points = 30.0
            alignment_label = "Aligned"
        elif is_misaligned:
            alignment_points = 0.0
            alignment_label = "Misaligned"
        else:
            alignment_points = 15.0
            alignment_label = "Neutral"

        # Livelihood Diversification
        if secondary_business_val != 'none':
            diversification_points = 10.0
        else:
            diversification_points = 0.0

        business_viability_score = biz_stability_points + alignment_points + diversification_points
        business_viability_score = max(0.0, min(100.0, business_viability_score))

        # ── 6. Final Score Aggregation (Weighted & Clamped) ───────────────────
        # Calculate raw float final score
        raw_final_score = (
            0.35 * financial_health_score +
            0.20 * housing_stability_score +
            0.15 * infrastructure_access_score +
            0.15 * household_burden_score +
            0.15 * business_viability_score
        )
        clamped_final_score = max(0.0, min(100.0, raw_final_score))
        
        # Rounded Final Integer Score (API boundary)
        final_score = round(clamped_final_score)

        # ── 7. Financial Health Floor Policy ──────────────────────────────────
        # Hard policy override: a Financial Health score below this threshold
        # rounds to 0 on the displayed component and cannot be compensated by
        # strong performance in other components.  The threshold is set to 0.5
        # so the gate fires precisely when the displayed score would be 0,
        # without relying on Python's banker's-rounding behaviour at the 0.5
        # boundary.  A borrower with zero or negligible financial health is
        # unconditionally assigned "Not Ready" regardless of other components.
        # Promoted to module-level constant so it can be surfaced via the
        # `thresholds` SSOT block below.
        FINANCIAL_HEALTH_FLOOR_THRESHOLD = 0.5
        is_floor_override = (
            financial_health_score < FINANCIAL_HEALTH_FLOOR_THRESHOLD
        )

        if is_floor_override:
            final_score = 0
            readiness_band = "Not Ready"
        else:
            # ── 8. Readiness Band Mapping ─────────────────────────────────────
            if final_score >= self.BAND_READY_MIN:
                readiness_band = "Ready"
            elif final_score >= self.BAND_MODERATELY_READY_MIN:
                readiness_band = "Moderately Ready"
            elif final_score >= self.BAND_NEEDS_IMPROVEMENT_MIN:
                readiness_band = "Needs Improvement"
            else:
                readiness_band = "Not Ready"

        # ── 9. Status and Factors ─────────────────────────────────────────────
        components_payload = {
            "financial_health": {
                "score": round(financial_health_score),
                "status": self._determine_status(financial_health_score),
                "weight": 0.35,
                "factors": {
                    "income_expense_ratio": round(income_expense_ratio, 4),
                    # When annual_income is 0 the ratio is undefined (inf); emit None
                    # so audit logs do not contain a misleading numeric value.
                    "loan_income_ratio": round(loan_income_ratio, 4) if math.isfinite(loan_income_ratio) else None
                }
            },
            "housing_stability": {
                "score": round(housing_stability_score),
                "status": self._determine_status(housing_stability_score),
                "weight": 0.20,
                "factors": {
                    "home_ownership": home_ownership_internal,
                    "house_type": house_type_internal,
                    "house_area": house_area
                }
            },
            "infrastructure_access": {
                "score": round(infrastructure_access_score),
                "status": self._determine_status(infrastructure_access_score),
                "weight": 0.15,
                "factors": {
                    "sanitary_availability": sanitary_avail == 1.0,
                    "water_availability": "Full" if water_avail == 1.0 else ("Partial" if water_avail == 0.5 else "None")
                }
            },
            "household_burden": {
                "score": round(household_burden_score),
                "status": self._determine_status(household_burden_score),
                "weight": 0.15,
                "factors": {
                    "total_dependents": young_dependents + old_dependents,
                    "dependents_per_occupant": round((young_dependents + old_dependents) / max(1, occupants_count), 4)
                }
            },
            "business_viability": {
                "score": round(business_viability_score),
                "status": self._determine_status(business_viability_score),
                "weight": 0.15,
                "factors": {
                    "primary_business": str(primary_business_raw) if primary_business_raw is not None else "Unknown",
                    "has_secondary_income": secondary_business_val != 'none',
                    "purpose_alignment": alignment_label
                }
            }
        }

        # ── 10. Mapped Features payload ───────────────────────────────────────
        mapped_features = {
            "primary_business_macro": primary_business_macro,
            "loan_purpose_macro": loan_purpose_macro,
            "type_of_house_internal": house_type_internal,
            "home_ownership_internal": home_ownership_internal
        }

        # ── 11. Threshold SSOT payload ─────────────────────────────────────────
        # The numeric cutoffs this engine consults, surfaced so downstream
        # explanation rules and audit logs can read them from a single source
        # rather than re-hardcoding the same literals.
        thresholds = {
            "financial_health_floor": float(FINANCIAL_HEALTH_FLOOR_THRESHOLD),
            "strong_status_min": int(self.STRONG_STATUS_MIN),
            "satisfactory_status_min": int(self.SATISFACTORY_STATUS_MIN),
            "band_ready_min": int(self.BAND_READY_MIN),
            "band_moderately_ready_min": int(self.BAND_MODERATELY_READY_MIN),
            "band_needs_improvement_min": int(self.BAND_NEEDS_IMPROVEMENT_MIN),
        }

        return {
            "score": final_score,
            "band": readiness_band,
            "components": components_payload,
            "mapped_features": mapped_features,
            "imputed_fields": imputed_fields,
            "policy_override_applied": is_floor_override,
            "thresholds": thresholds,
        }

def get_readiness_score(features: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience wrapper for the Readiness Engine."""
    engine = ReadinessEngine()
    return engine.calculate_readiness(features)
