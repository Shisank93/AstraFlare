"""
Unit and Integration Tests for Phase 3.9.2 Pre-ML Scientific Validation Auditor.
"""
import pytest
from data_pipeline.sources.audit_scientific_validation import scientific_auditor, ScientificValidationAuditor

def test_concrete_clustering_examples_structure():
    """Verify concrete clustering cases generation for 5 key edge cases."""
    examples = scientific_auditor.audit_concrete_clustering_examples()
    assert len(examples) == 5
    case_types = [e["case_type"] for e in examples]
    assert "Singleton Event" in case_types
    assert "Valid Multi-Observation Event" in case_types
    assert "Transitive A-B-C Cluster Case" in case_types
    assert "Cross-Satellite Multi-Sensor Event" in case_types
    assert "Near Threshold Boundary Case" in case_types

def test_feature_circularity_classification():
    """Verify feature circularity risk classifications."""
    circ_matrix = scientific_auditor.audit_feature_circularity_matrix()
    assert len(circ_matrix) >= 15
    
    # Check that industrial_distance_m is flagged with high risk
    dist_row = [r for r in circ_matrix if r["feature"] == "industrial_distance_m"][0]
    assert "HIGH_CIRCULARITY" in dist_row["risk"]
    
    # Check that duration_hours is independent
    dur_row = [r for r in circ_matrix if r["feature"] == "duration_hours"][0]
    assert "INDEPENDENT" in dur_row["classification"]
