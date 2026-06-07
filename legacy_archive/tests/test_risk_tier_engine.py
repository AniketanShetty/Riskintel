import unittest
import sys
import os

# Add the backend/app directory to the path so we can import the engine
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

from engines.risk_tier.risk_tier_engine import RiskTierEngine, get_risk_tier


class TestRiskTierEngine(unittest.TestCase):
    """Test cases for the RiskTierEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = RiskTierEngine()

    def test_p1_tier(self):
        """Test scores that fall into P1 tier (>= 701)."""
        # Test boundary and above
        self.assertEqual(self.engine.determine_risk_tier(701)['risk_tier'], 'P1')
        self.assertEqual(self.engine.determine_risk_tier(720)['risk_tier'], 'P1')
        self.assertEqual(self.engine.determine_risk_tier(800)['risk_tier'], 'P1')

    def test_p2_tier(self):
        """Test scores that fall into P2 tier (>= 669 and < 701)."""
        # Test boundaries and middle
        self.assertEqual(self.engine.determine_risk_tier(669)['risk_tier'], 'P2')
        self.assertEqual(self.engine.determine_risk_tier(685)['risk_tier'], 'P2')
        self.assertEqual(self.engine.determine_risk_tier(700)['risk_tier'], 'P2')

    def test_p4_tier(self):
        """Test scores that fall into P4 tier (<= 658)."""
        # Test boundaries and below
        self.assertEqual(self.engine.determine_risk_tier(658)['risk_tier'], 'P4')
        self.assertEqual(self.engine.determine_risk_tier(650)['risk_tier'], 'P4')
        self.assertEqual(self.engine.determine_risk_tier(600)['risk_tier'], 'P4')
        self.assertEqual(self.engine.determine_risk_tier(0)['risk_tier'], 'P4')

    def test_p3_tier_fallback(self):
        """Test scores that fall into P3 tier (fallback: 659-668)."""
        # Test the entire fallback range
        for score in range(659, 669):
            with self.subTest(score=score):
                self.assertEqual(self.engine.determine_risk_tier(score)['risk_tier'], 'P3')

    def test_tier_descriptions(self):
        """Test that each tier returns the correct description."""
        # P1
        self.assertIn('Low Risk', self.engine.determine_risk_tier(701)['tier_description'])
        # P2
        self.assertIn('Moderate Risk', self.engine.determine_risk_tier(680)['tier_description'])
        # P4
        self.assertIn('High Risk', self.engine.determine_risk_tier(650)['tier_description'])
        # P3
        self.assertIn('Elevated Risk', self.engine.determine_risk_tier(660)['tier_description'])

    def test_get_risk_tier_convenience_function(self):
        """Test the convenience function get_risk_tier."""
        # Test a few scores
        self.assertEqual(get_risk_tier(650)['risk_tier'], 'P4')
        self.assertEqual(get_risk_tier(660)['risk_tier'], 'P3')
        self.assertEqual(get_risk_tier(680)['risk_tier'], 'P2')
        self.assertEqual(get_risk_tier(701)['risk_tier'], 'P1')

    def test_invalid_score_type(self):
        """Test that the engine handles non-integer scores appropriately."""
        # The current implementation expects an integer. We'll test that it raises a TypeError
        # when given a string, but note: the engine doesn't currently validate type.
        # Since the requirement doesn't specify, we'll skip this for now or adjust if needed.
        # For now, we'll just note that the engine will likely throw a TypeError when comparing string to int.
        with self.assertRaises(TypeError):
            self.engine.determine_risk_tier("invalid")

    def test_thresholds_loading(self):
        """Test that thresholds are loaded correctly from the JSON file."""
        # Check that the thresholds are loaded and have the expected structure
        self.assertIn('P1', self.engine.thresholds)
        self.assertIn('P2', self.engine.thresholds)
        self.assertIn('P3', self.engine.thresholds)
        self.assertIn('P4', self.engine.thresholds)

        # Check specific values
        self.assertEqual(self.engine.thresholds['P1']['min_score'], 701)
        self.assertEqual(self.engine.thresholds['P2']['min_score'], 669)
        self.assertEqual(self.engine.thresholds['P2']['max_score'], 700)
        self.assertEqual(self.engine.thresholds['P4']['max_score'], 658)

    def test_missing_threshold_file(self):
        """Test that a missing thresholds file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            RiskTierEngine(thresholds_path="non_existent_file.json")


if __name__ == '__main__':
    unittest.main()
