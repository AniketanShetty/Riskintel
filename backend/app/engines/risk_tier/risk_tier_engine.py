"""Risk Tier Engine Module
Determines risk tiers based on scores and configurable thresholds."""
import json
import os
from typing import Dict, Any, Optional


class RiskTierEngine:
    """Engine for determining risk tiers based on scores."""
    
    _cached_thresholds = None
    _cached_path = None
    
    def __init__(self, thresholds_path: Optional[str] = None):
        """
        Initialize the risk tier engine.
        
        Args:
            thresholds_path: Path to the thresholds JSON file. 
                           If None, uses default path.
        """
        if thresholds_path is None:
            # Default path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            thresholds_path = os.path.join(
                current_dir, '..', '..', '..', '..', 
                'data', 'processed', 'risk_tier_thresholds.json'
            )
        
        self.thresholds_path = thresholds_path
        
        if RiskTierEngine._cached_thresholds is not None and RiskTierEngine._cached_path == thresholds_path:
            self.thresholds = RiskTierEngine._cached_thresholds
        else:
            self.thresholds = self._load_thresholds()
            RiskTierEngine._cached_thresholds = self.thresholds
            RiskTierEngine._cached_path = thresholds_path
    
    def _load_thresholds(self) -> Dict[str, Any]:
        """Load risk tier thresholds from JSON file."""
        try:
            with open(self.thresholds_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Thresholds file not found: {self.thresholds_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in thresholds file: {e}")
    
    def determine_risk_tier(self, score: int) -> Dict[str, str]:
        """
        Determine risk tier based on score.
        
        Args:
            score: Integer score to evaluate
            
        Returns:
            Dictionary with risk_tier and tier_description
        """
        # Check P1: score >= 701
        if score >= self.thresholds['P1']['min_score']:
            return {
                "risk_tier": "P1",
                "tier_description": self.thresholds['P1'].get('description', 'Highest risk tier')
            }
        
        # Check P2: score >= 669 and < 701 (i.e., up to 700 inclusive)
        p2_min = self.thresholds['P2']['min_score']
        p2_max = self.thresholds['P2']['max_score']
        if p2_min <= score <= p2_max:
            return {
                "risk_tier": "P2",
                "tier_description": self.thresholds['P2'].get('description', 'High risk tier')
            }
        
        # Check P4: score <= 658
        p4_max = self.thresholds['P4']['max_score']
        if score <= p4_max:
            return {
                "risk_tier": "P4",
                "tier_description": self.thresholds['P4'].get('description', 'Low risk tier')
            }
        
        # Fallback to P3: scores 659-668
        return {
            "risk_tier": "P3",
            "tier_description": self.thresholds['P3'].get('description', 'Moderate risk tier (fallback)')
        }


def get_risk_tier(score: int) -> Dict[str, str]:
    """
    Convenience function to determine risk tier.
    
    Args:
        score: Integer score to evaluate
        
    Returns:
        Dictionary with risk_tier and tier_description
    """
    engine = RiskTierEngine()
    return engine.determine_risk_tier(score)


if __name__ == "__main__":
    # Example usage
    engine = RiskTierEngine()
    test_scores = [650, 660, 670, 680, 690, 700, 701, 720]
    
    print("Risk Tier Determination Examples:")
    print("=" * 40)
    for score in test_scores:
        result = engine.determine_risk_tier(score)
        print(f"Score: {score:>4} -> Tier: {result['risk_tier']} ({result['tier_description']})")
