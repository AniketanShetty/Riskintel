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
    
    def determine_risk_tier(self, score: int) -> Dict[str, Any]:
        """
        Determine risk tier based on score.

        Args:
            score: Integer score to evaluate

        Returns:
            Dictionary with:
              - risk_tier: "P1" | "P2" | "P3" | "P4"
              - tier_description: human-readable description
              - thresholds: numeric SSOT values actually consulted by this
                engine (p1_min, p2_min, p2_max, p4_max). P3 is the implicit
                band between p2_max and p4_max, so we derive p3_min and
                p3_max from the surrounding values rather than hardcoding.
        """
        p1_min = int(self.thresholds['P1']['min_score'])
        p2_min = int(self.thresholds['P2']['min_score'])
        p2_max = int(self.thresholds['P2']['max_score'])
        p4_max = int(self.thresholds['P4']['max_score'])
        # P3 is the implicit fallback band between P4 and P2 (not in JSON).
        # P2 occupies [p2_min, p2_max]; P4 occupies (-inf, p4_max].
        # P3 = (p4_max, p2_min), exclusive on the P4 side, inclusive on P2 side.
        p3_min = p4_max + 1
        p3_max = p2_min - 1

        thresholds = {
            "p1_min": p1_min,
            "p2_min": p2_min,
            "p2_max": p2_max,
            "p3_min": p3_min,
            "p3_max": p3_max,
            "p4_max": p4_max,
        }

        # Check P1: score >= p1_min
        if score >= p1_min:
            return {
                "risk_tier": "P1",
                "tier_description": self.thresholds['P1'].get('description', 'Highest risk tier'),
                "thresholds": thresholds,
            }

        # Check P2: p2_min <= score <= p2_max
        if p2_min <= score <= p2_max:
            return {
                "risk_tier": "P2",
                "tier_description": self.thresholds['P2'].get('description', 'High risk tier'),
                "thresholds": thresholds,
            }

        # Check P4: score <= p4_max
        if score <= p4_max:
            return {
                "risk_tier": "P4",
                "tier_description": self.thresholds['P4'].get('description', 'Low risk tier'),
                "thresholds": thresholds,
            }

        # Fallback to P3: scores p3_min-p3_max
        return {
            "risk_tier": "P3",
            "tier_description": self.thresholds['P3'].get('description', 'Moderate risk tier (fallback)'),
            "thresholds": thresholds,
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
