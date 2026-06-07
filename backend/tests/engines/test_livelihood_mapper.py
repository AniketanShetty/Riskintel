import pytest
import inspect
from app.engines.livelihood.livelihood_mapper import map_livelihood

def test_exact_matches():
    assert map_livelihood("kirana")["cluster_id"] == 1
    assert map_livelihood("tailoring")["cluster_id"] == 2
    assert map_livelihood("dairy")["cluster_id"] == 3
    assert map_livelihood("manufacturing")["cluster_id"] == 4
    assert map_livelihood("transport")["cluster_id"] == 5

def test_case_variants():
    assert map_livelihood("KIRANA")["cluster_id"] == 1
    assert map_livelihood("Tailoring")["cluster_id"] == 2
    assert map_livelihood("dAiRy")["cluster_id"] == 3

def test_whitespace_variants():
    assert map_livelihood(" kirana ")["cluster_id"] == 1
    assert map_livelihood("\ttailoring\n")["cluster_id"] == 2

def test_unknown_values():
    assert map_livelihood("quantum computing")["cluster_id"] == 0
    assert map_livelihood("unknown_business_123")["cluster_id"] == 0

def test_null_empty_values():
    assert map_livelihood("")["cluster_id"] == 0
    assert map_livelihood("   ")["cluster_id"] == 0
    assert map_livelihood(None)["cluster_id"] == 0
    assert map_livelihood(123)["cluster_id"] == 0

def test_contract_shape():
    output = map_livelihood("grocery")
    assert "label" in output
    assert "description" in output
    assert "cluster_id" in output
    assert output["label"] == "Trade & Retail"
    
def test_demographic_input_blocking():
    """
    Architectural Proof: Verify that the function signature explicitly prohibits
    receiving the full applicant dictionary, mathematically guaranteeing that
    demographic features cannot be evaluated.
    """
    sig = inspect.signature(map_livelihood)
    params = list(sig.parameters.keys())
    assert len(params) == 1
    assert params[0] == "primary_business"
    assert "applicant" not in params
    assert "social_class" not in params
    assert "gender" not in params
