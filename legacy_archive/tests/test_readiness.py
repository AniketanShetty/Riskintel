import unittest
import sys
import os

# Add the backend/app directory to the path so we can import the engine
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

from engines.readiness.readiness_engine import ReadinessEngine, get_readiness_score

class TestReadinessEngine(unittest.TestCase):
    """Test cases for the ReadinessEngine (E5)."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = ReadinessEngine()
        # Define a standard high-quality baseline payload
        self.baseline_features = {
            "annual_income": 120000.0,
            "monthly_expenses": 2000.0,
            "loan_amount": 30000.0,
            "home_ownership": "owned",
            "type_of_house": "pucca",
            "house_area": 450.0,
            "sanitary_availability": 1.0,
            "water_availability": 1.0,
            "young_dependents": 0,
            "old_dependents": 0,
            "occupants_count": 2,
            "primary_business": "Retail shop",
            "secondary_business": "none",
            "loan_purpose": "working capital"
        }

    def test_high_quality_ready_applicant(self):
        """Test that a high-quality applicant achieves 'Ready' band."""
        res = self.engine.calculate_readiness(self.baseline_features)
        
        # income_expense_ratio = 120000 / (2000 * 12) = 5.0 (> 3.0 -> Stability=100)
        # loan_income_ratio = 30000 / 120000 = 0.25 (<= 1.5 -> Debt Burden = 100*(1.5-0.25)/1.5 = 83.33)
        # Fin Health = 0.5 * 100 + 0.5 * 83.33 = 91.67
        
        # Housing: owned(40) + T1(40) + area(15) = 95.0
        # Infra: sanitation(50) + water(50) = 100.0
        # Burden: 100 - (0 + 0 + 0) = 100.0
        # Viability: Retail(60) + Aligned(30) + No diversification(0) = 90.0
        
        # Weighted Score = 0.35*91.67 + 0.20*95 + 0.15*100 + 0.15*100 + 0.15*90 = 94.58
        # Rounded: 95
        
        self.assertEqual(res["score"], 95)
        self.assertEqual(res["band"], "Ready")
        self.assertEqual(res["components"]["financial_health"]["score"], 92)
        self.assertEqual(res["components"]["financial_health"]["status"], "Strong")
        self.assertEqual(res["components"]["housing_stability"]["score"], 95)
        self.assertEqual(res["components"]["housing_stability"]["status"], "Strong")
        self.assertEqual(res["components"]["infrastructure_access"]["score"], 100)
        self.assertEqual(res["components"]["infrastructure_access"]["status"], "Strong")
        self.assertEqual(res["components"]["household_burden"]["score"], 100)
        self.assertEqual(res["components"]["household_burden"]["status"], "Strong")
        self.assertEqual(res["components"]["business_viability"]["score"], 90)
        self.assertEqual(res["components"]["business_viability"]["status"], "Strong")
        self.assertFalse(res["policy_override_applied"])
        self.assertEqual(len(res["imputed_fields"]), 0)

    def test_financial_health_floor_policy(self):
        """Test that if Financial Health score is 0, the final score and band are overridden."""
        features = self.baseline_features.copy()
        # Make debt burden huge to drop score to 0 (loan-to-income > 1.5)
        features["loan_amount"] = 300000.0
        features["annual_income"] = 50000.0
        features["monthly_expenses"] = 10000.0
        # income_expense_ratio = 50000 / 120000 = 0.41 (< 1.0 -> Stability = 0)
        # loan_income_ratio = 300000 / 50000 = 6.0 (> 1.5 -> Debt Burden = 0)
        # Fin Health = 0.0
        
        res = self.engine.calculate_readiness(features)
        
        self.assertEqual(res["score"], 0)
        self.assertEqual(res["band"], "Not Ready")
        self.assertTrue(res["policy_override_applied"])
        self.assertEqual(res["components"]["financial_health"]["score"], 0)
        self.assertEqual(res["components"]["financial_health"]["status"], "Needs Attention")

    def test_imputation_tracking(self):
        """Test default values and imputation tracking for missing fields."""
        features = self.baseline_features.copy()
        del features["house_area"]
        del features["secondary_business"]
        
        res = self.engine.calculate_readiness(features)
        
        self.assertIn("house_area", res["imputed_fields"])
        self.assertIn("secondary_business", res["imputed_fields"])
        self.assertEqual(res["components"]["housing_stability"]["factors"]["house_area"], 450.0)
        self.assertFalse(res["components"]["business_viability"]["factors"]["has_secondary_income"])

    def test_house_type_and_ownership_translations(self):
        """Test string/numeric translations for house type and home ownership."""
        features = self.baseline_features.copy()
        features["type_of_house"] = "pucca"
        features["home_ownership"] = 1.0 # Mapped to owned
        
        res = self.engine.calculate_readiness(features)
        self.assertEqual(res["components"]["housing_stability"]["factors"]["house_type"], "T1")
        self.assertEqual(res["components"]["housing_stability"]["factors"]["home_ownership"], "owned")

        features2 = self.baseline_features.copy()
        features2["type_of_house"] = "semi_pucca"
        features2["home_ownership"] = 0.0 # Mapped to rented
        res2 = self.engine.calculate_readiness(features2)
        self.assertEqual(res2["components"]["housing_stability"]["factors"]["house_type"], "T2")
        self.assertEqual(res2["components"]["housing_stability"]["factors"]["home_ownership"], "rented")

    def test_validation_rules(self):
        """Test that validation rules correctly raise ValueError on invalid inputs."""
        # Negative annual income
        features = self.baseline_features.copy()
        features["annual_income"] = -1000.0
        with self.assertRaises(ValueError):
            self.engine.calculate_readiness(features)

        # Negative monthly expenses
        features = self.baseline_features.copy()
        features["monthly_expenses"] = -10.0
        with self.assertRaises(ValueError):
            self.engine.calculate_readiness(features)

        # Negative house area
        features = self.baseline_features.copy()
        features["house_area"] = -150.0
        with self.assertRaises(ValueError):
            self.engine.calculate_readiness(features)

        # Occupants count violation (occupants < dependents + 1)
        features = self.baseline_features.copy()
        features["young_dependents"] = 3
        features["old_dependents"] = 1
        features["occupants_count"] = 3 # Needs to be at least 5 (3 + 1 + 1)
        with self.assertRaises(ValueError):
            self.engine.calculate_readiness(features)

    def test_new_readiness_validations_and_translations(self):
        """Test the new validations and runtime translations added for Readiness Engine."""
        # 1. water_availability=10 (Invalid value)
        features = self.baseline_features.copy()
        features["water_availability"] = 10
        with self.assertRaises(ValueError):
            self.engine.calculate_readiness(features)

        # 2. water_availability=-1 (Invalid value)
        features = self.baseline_features.copy()
        features["water_availability"] = -1
        with self.assertRaises(ValueError):
            self.engine.calculate_readiness(features)

        # 3. water_availability="partial" (Valid runtime translation)
        features = self.baseline_features.copy()
        features["water_availability"] = "partial"
        res = self.engine.calculate_readiness(features)
        # Should succeed and set water_availability factor to 'Partial' (since 0.5 is mapped)
        self.assertEqual(res["components"]["infrastructure_access"]["factors"]["water_availability"], "Partial")
        
        # Check water_availability = "none" and "full"
        features["water_availability"] = "none"
        res_none = self.engine.calculate_readiness(features)
        self.assertEqual(res_none["components"]["infrastructure_access"]["factors"]["water_availability"], "None")
        
        features["water_availability"] = "full"
        res_full = self.engine.calculate_readiness(features)
        self.assertEqual(res_full["components"]["infrastructure_access"]["factors"]["water_availability"], "Full")

        # 4. sanitary_availability=5 (Invalid value)
        features = self.baseline_features.copy()
        features["sanitary_availability"] = 5
        with self.assertRaises(ValueError):
            self.engine.calculate_readiness(features)

        # 5. Invalid home ownership (e.g. "invalid_ownership")
        features = self.baseline_features.copy()
        features["home_ownership"] = "invalid_ownership"
        with self.assertRaises(ValueError):
            self.engine.calculate_readiness(features)

        # 6. Invalid house type (e.g. "invalid_house")
        features = self.baseline_features.copy()
        features["type_of_house"] = "invalid_house"
        with self.assertRaises(ValueError):
            self.engine.calculate_readiness(features)

    def test_nan_inf_and_zero_income_fixes(self):
        """Test that NaN and Infinity values are rejected, and zero annual income forces financial health to 0."""
        # 1. NaN checks on numeric inputs
        for field in [
            'annual_income', 'monthly_expenses', 'loan_amount', 'house_area',
            'sanitary_availability', 'water_availability', 'young_dependents',
            'old_dependents', 'occupants_count'
        ]:
            features = self.baseline_features.copy()
            features[field] = float('nan')
            with self.assertRaises(ValueError):
                self.engine.calculate_readiness(features)

        # 2. Infinity checks on numeric inputs
        for field in [
            'annual_income', 'monthly_expenses', 'loan_amount', 'house_area',
            'sanitary_availability', 'water_availability', 'young_dependents',
            'old_dependents', 'occupants_count'
        ]:
            for inf_val in [float('inf'), float('-inf')]:
                features = self.baseline_features.copy()
                features[field] = inf_val
                with self.assertRaises(ValueError):
                    self.engine.calculate_readiness(features)

        # 3. Annual income <= 0 forces Financial Health = 0 (and forces floor policy override to trigger)
        features_zero_income = self.baseline_features.copy()
        features_zero_income['annual_income'] = 0.0
        features_zero_income['loan_amount'] = 0.0 # previously bypassed override when loan_amount = 0.0
        res = self.engine.calculate_readiness(features_zero_income)
        self.assertEqual(res["components"]["financial_health"]["score"], 0)
        self.assertEqual(res["score"], 0)
        self.assertEqual(res["band"], "Not Ready")
        self.assertTrue(res["policy_override_applied"])

    def test_type_error_rejections(self):
        """Test that TypeError is caught and converted to ValueError for complex types."""
        # 1. TypeError checks on core financial inputs
        for field in ['annual_income', 'monthly_expenses', 'loan_amount']:
            features = self.baseline_features.copy()
            features[field] = {'amount': 100} # complex dict type
            with self.assertRaises(ValueError) as ctx:
                self.engine.calculate_readiness(features)
            self.assertIn("must be valid numbers", str(ctx.exception))

        # 2. TypeError check on house_area
        features = self.baseline_features.copy()
        features['house_area'] = {'val': 450} # complex dict type
        with self.assertRaises(ValueError) as ctx:
            self.engine.calculate_readiness(features)
        self.assertIn("house_area must be a valid number", str(ctx.exception))

        # 3. TypeError check on dependents and occupants
        for field in ['young_dependents', 'old_dependents', 'occupants_count']:
            features = self.baseline_features.copy()
            features[field] = {'count': 2} # complex dict type
            with self.assertRaises(ValueError) as ctx:
                self.engine.calculate_readiness(features)
            self.assertIn("must be integers", str(ctx.exception))

    def test_business_viability_mappings(self):
        """Test macro-categorization and alignment logic."""
        features = self.baseline_features.copy()
        features["primary_business"] = "dairy farming and cows" # Mapped to Agriculture
        features["loan_purpose"] = "livestock purchase" # Mapped to Agriculture
        
        res = self.engine.calculate_readiness(features)
        self.assertEqual(res["mapped_features"]["primary_business_macro"], "Agriculture")
        self.assertEqual(res["mapped_features"]["loan_purpose_macro"], "Agriculture")
        self.assertEqual(res["components"]["business_viability"]["factors"]["purpose_alignment"], "Aligned")

    def test_convenience_function(self):
        """Test the get_readiness_score convenience wrapper."""
        res = get_readiness_score(self.baseline_features)
        self.assertEqual(res["score"], 95)
        self.assertEqual(res["band"], "Ready")

    def test_defect_fixes(self):
        """Tests covering the five confirmed E5 defects and their fixes."""

        # ── Fix 1: loan_income_ratio denominator no longer clamped to 1.0 ─────
        # annual_income=0.5, loan_amount=1.0 → true ratio = 2.0 > 1.5 → debt_burden = 0.
        # Old engine used max(1.0, 0.5)=1.0 giving ratio=1.0, which yielded score ~33.
        features = self.baseline_features.copy()
        features["annual_income"] = 0.5
        features["loan_amount"] = 1.0
        features["monthly_expenses"] = 0.001  # tiny expenses to isolate debt burden path
        res = self.engine.calculate_readiness(features)
        # True ratio is 1.0/0.5 = 2.0 > 1.5 → debt_burden_ratio_score = 0
        # income_expense_ratio = 0.5/(max(1,0.001)*12) = 0.5/12 < 1 → stability = 0
        # financial_health = 0 → floor override must fire
        self.assertTrue(res["policy_override_applied"],
                        "loan 2x income should trigger floor override with corrected denominator")
        self.assertEqual(res["score"], 0)
        self.assertEqual(res["band"], "Not Ready")
        actual_ratio = res["components"]["financial_health"]["factors"]["loan_income_ratio"]
        # With the fix the reported ratio is 1.0/0.5 = 2.0 (NOT the old clamped value of 1.0)
        self.assertEqual(actual_ratio, 2.0,
            "loan_income_ratio must use actual income as denominator (not clamped to 1.0)")

        # ── Fix 2: floor override fires when financial_health rounds to 0 ─────
        # annual_income=12.01, monthly_expenses=12.0, loan_amount=18.0
        # income_expense_ratio = 12.01/144 ≈ 0.083 < 1 → stability = 0
        # loan_income_ratio = 18/12.01 ≈ 1.499 < 1.5 → debt_burden ≈ 0.083
        # financial_health ≈ 0.041 → rounds to 0 → override MUST fire now
        features2 = self.baseline_features.copy()
        features2["annual_income"] = 12.01
        features2["monthly_expenses"] = 12.0
        features2["loan_amount"] = 18.0
        res2 = self.engine.calculate_readiness(features2)
        self.assertEqual(res2["components"]["financial_health"]["score"], 0,
                         "displayed financial_health score should be 0")
        self.assertTrue(res2["policy_override_applied"],
                        "round-to-zero financial_health must trigger floor override")
        self.assertEqual(res2["band"], "Not Ready")

        # ── Fix 3: audit factors emit None for undefined loan_income_ratio ────
        # When annual_income=0 the ratio is mathematically undefined (infinity).
        # The factors payload must carry None, not a spurious numeric value.
        features3 = self.baseline_features.copy()
        features3["annual_income"] = 0.0
        features3["loan_amount"] = 50000.0
        res3 = self.engine.calculate_readiness(features3)
        self.assertTrue(res3["policy_override_applied"])
        self.assertIsNone(
            res3["components"]["financial_health"]["factors"]["loan_income_ratio"],
            "loan_income_ratio must be None when annual_income is 0 (undefined ratio)"
        )

        # ── Fix 4: multi-element list input raises a clean ValueError ─────────
        # Previously pd.isna([a, b]) returned np.array([False, False]) whose
        # bool() evaluation leaked a NumPy "ambiguous truth value" ValueError.
        # Now the isinstance guard skips pd.isna for non-scalars, so the error
        # comes from the downstream float() conversion block with a clear message.
        for field in ["annual_income", "monthly_expenses", "loan_amount"]:
            features4 = self.baseline_features.copy()
            features4[field] = [100.0, 200.0]  # two-element list
            with self.assertRaises(ValueError) as ctx:
                self.engine.calculate_readiness(features4)
            self.assertNotIn(
                "truth value of an array", str(ctx.exception),
                f"NumPy ambiguous-array message must not leak for field '{field}'"
            )

if __name__ == '__main__':
    unittest.main()
