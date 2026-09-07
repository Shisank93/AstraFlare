"""
AstraFlare Evidence-Based Thermal Anomaly Risk Engine — Evidence Extraction & Traceability.
Provides audit-ready traceability for every dimensional score contribution and evidence item.
"""
from typing import List, Dict, Any
from backend.risk_engine.models import EvidenceItem, EvidenceBreakdown, RiskInput
from backend.risk_engine.config import RiskEngineConfig


class EvidenceExtractor:
    """Extracts, formats, and validates traceable evidence items."""

    def compile_evidence_summary(self, items: List[EvidenceItem]) -> List[Dict[str, Any]]:
        """Formats evidence items into structured dictionary representation."""
        summary = []
        for item in items:
            summary.append(item.model_dump())
        return summary

    def format_traceability_table(self, items: List[EvidenceItem]) -> List[Dict[str, Any]]:
        """Extracts mathematical traceability records for demonstration and analyst auditing."""
        records = []
        for item in items:
            records.append({
                "feature": item.input_feature,
                "raw_value": str(item.input_value),
                "normalization": round(item.normalization, 4),
                "weight": round(item.weight, 4),
                "contribution": round(item.contribution, 4),
                "type": item.type,
                "strength": item.strength
            })
        return records


evidence_extractor = EvidenceExtractor()
