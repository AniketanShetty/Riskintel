from dataclasses import dataclass
from typing import Callable, Dict, Any, Optional

@dataclass
class ExplanationRule:
    rule_id: str
    feature_name: str
    priority: int
    condition_callable: Callable[[Dict[str, Any]], bool]
    evidence_callable: Callable[[Dict[str, Any]], str]
    reason_template: str
    advice_template: str
    format_args_callable: Callable[[Dict[str, Any]], Dict[str, Any]]
    advice_type: str = "generic"
    evidence_sources: Optional[list] = None
