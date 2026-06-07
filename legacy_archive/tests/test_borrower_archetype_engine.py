import unittest
import sys
import os

# Add the backend/app directory to the path so we can import the engine
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

from engines.archetype.borrower_archetype_engine import BorrowerArchetypeEngine, get_borrower_archetype

class TestBorrowerArchetypeEngine(unittest.TestCase):
    """Test cases for the BorrowerArchetypeEngine."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.engine = BorrowerArchetypeEngine()

    def test_archetype_preprocessing(self):
        """Verify that EDUCATION string correctly maps to its integer."""
        self.assertEqual(self.engine._map_education('UNDER GRADUATE'), 3)
        self.assertEqual(self.engine._map_education('PROFESSIONAL'), 6)
        self.assertEqual(self.engine._map_education('10TH'), 1)
        self.assertEqual(self.engine._map_education('RANDOM_UNKNOWN'), 0)
        self.assertEqual(self.engine._map_education(None), 0)

    def test_archetype_inference(self):
        """Ensure that raw user inputs pass through the pipeline and return a valid persona."""
        features = {
            'NETMONTHLYINCOME': 50000,
            'AGE': 35,
            'Time_With_Curr_Empr': 60,
            'EDUCATION': 'GRADUATE'
        }
        
        result = get_borrower_archetype(features)
        
        self.assertIn("cluster_id", result)
        self.assertIn("archetype_label", result)
        self.assertTrue(isinstance(result["cluster_id"], int))
        self.assertTrue(isinstance(result["archetype_label"], str))

    def test_credit_score_exclusion(self):
        """Verify that the engine ignores Credit_Score if mistakenly passed."""
        features = {
            'NETMONTHLYINCOME': 30000,
            'AGE': 25,
            'Time_With_Curr_Empr': 24,
            'EDUCATION': 'UNDER GRADUATE',
            'Credit_Score': 800  # Should be ignored
        }
        
        result = get_borrower_archetype(features)
        
        # It shouldn't crash, should just return a valid response
        self.assertIn("archetype_label", result)

    def test_invalid_numeric_inputs(self):
        """Test with invalid numerical inputs."""
        features = {
            'NETMONTHLYINCOME': 'invalid',
            'AGE': 35,
            'Time_With_Curr_Empr': 60,
            'EDUCATION': 'GRADUATE'
        }
        with self.assertRaises(ValueError):
            self.engine.determine_archetype(features)

if __name__ == '__main__':
    unittest.main()
