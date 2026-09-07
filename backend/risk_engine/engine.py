"""
AstraFlare Evidence-Based Thermal Anomaly Risk Engine — Master Engine Entry Point.
Executes multi-factor evidence fusion, deterministic operational risk scoring,
dimensional sub-scoring, conflict detection, and human review routing.
"""
from typing import Union, Dict, Any
from backend.risk_engine.config import RiskEngineConfig, default_config
from backend.risk_engine.models import (
    RiskInput, RiskAssessment, EvidenceItem, EvidenceBreakdown
)
from backend.risk_engine.scoring import (
    score_thermal_intensity, score_historical_anomaly, score_industrial_proximity,
    score_industrial_density, score_natural_context, score_recurrence_and_persistence
)
from backend.risk_engine.quality import evaluate_data_quality
from backend.risk_engine.conflict import evaluate_evidence_conflict_and_context


class EvidenceRiskEngine:
    """Master Evidence-Based Thermal Anomaly Risk Engine."""

    def __init__(self, config: RiskEngineConfig = default_config):
        self.config = config
        assert self.config.validate_weights(), "RiskEngineConfig weights must sum to 1.0"

    def assess_event(self, input_data: Union[RiskInput, Dict[str, Any]]) -> RiskAssessment:
        """
        Executes deterministic operational risk assessment over event feature vector.
        Input: RiskInput pydantic model OR dictionary.
        Output: Complete RiskAssessment model.
        """
        if isinstance(input_data, dict):
            # Parse dict safely into RiskInput model
            inp = RiskInput(**input_data)
        else:
            inp = input_data

        cfg = self.config
        all_evidence: List[EvidenceItem] = []

        # 1. Thermal Intensity Dimension
        thermal_score, ev_thermal = score_thermal_intensity(inp, cfg)
        all_evidence.extend(ev_thermal)

        # 2. Historical Anomaly Dimension
        hist_anomaly_score, history_status, ev_hist = score_historical_anomaly(inp, cfg)
        all_evidence.extend(ev_hist)

        # 3. Industrial Proximity Dimension
        ind_prox_score, ev_prox = score_industrial_proximity(inp, cfg)
        all_evidence.extend(ev_prox)

        # 4. Industrial Site Density Dimension
        ind_dens_score, ev_dens = score_industrial_density(inp, cfg)
        all_evidence.extend(ev_dens)
        ind_context_score = round(min(1.0, max(0.0, ind_prox_score * 0.70 + ind_dens_score * 0.30)), 4)

        # 5. Natural / Wildland Land Cover Dimension
        nat_score, land_interp, ev_nat = score_natural_context(inp, cfg)
        all_evidence.extend(ev_nat)

        # 6. Recurrence & Persistence Dimension
        rec_score, pers_score, ev_rec = score_recurrence_and_persistence(inp, cfg)
        all_evidence.extend(ev_rec)

        # 7. Telemetry & GIS Data Quality
        quality_score, quality_status, ev_qual = evaluate_data_quality(inp, cfg)
        all_evidence.extend(ev_qual)

        # 8. Deterministic Composite Overall Risk Score
        overall_risk_score = (
            thermal_score * cfg.thermal_weight +
            hist_anomaly_score * cfg.historical_weight +
            ind_prox_score * (cfg.industrial_weight * 0.70) +
            ind_dens_score * (cfg.industrial_weight * 0.30) +
            rec_score * cfg.recurrence_weight +
            nat_score * cfg.natural_weight +
            quality_score * cfg.quality_weight
        )
        overall_risk_score = round(min(1.0, max(0.0, overall_risk_score)), 4)

        # 9. Operational Risk Level (LOW, MEDIUM, HIGH)
        if overall_risk_score > cfg.risk_medium_max:
            risk_level = "HIGH"
        elif overall_risk_score > cfg.risk_low_max:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # 10. Conflict Detection & Context Resolution
        evidence_status, likely_context, human_review_required, human_review_reasons = (
            evaluate_evidence_conflict_and_context(
                inp, ind_prox_score, ind_dens_score, nat_score, hist_anomaly_score,
                rec_score, pers_score, quality_score, quality_status,
                overall_risk_score, cfg
            )
        )

        # 11. Investigation Priority (LOW, MEDIUM, HIGH, URGENT)
        if overall_risk_score >= 0.70 and evidence_status in ("STRONG_INDUSTRIAL_CONTEXT", "UNUSUAL_THERMAL_ACTIVITY", "CONFLICTING_EVIDENCE") and quality_status in ("HIGH", "MEDIUM"):
            investigation_priority = "URGENT"
        elif overall_risk_score >= 0.65 or ind_prox_score >= 0.75 or (nat_score >= 0.80 and thermal_score >= 0.50):
            investigation_priority = "HIGH"
        elif overall_risk_score >= 0.40:
            investigation_priority = "MEDIUM"
        else:
            investigation_priority = "LOW"

        return RiskAssessment(
            event_id=inp.event_id,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            investigation_priority=investigation_priority,
            industrial_context_score=ind_context_score,
            natural_fire_context_score=nat_score,
            thermal_anomaly_score=thermal_score,
            historical_anomaly_score=hist_anomaly_score,
            recurrence_score=rec_score,
            persistence_score=pers_score,
            data_quality_score=quality_score,
            history_status=history_status,
            data_quality_status=quality_status,
            evidence_status=evidence_status,
            likely_context=likely_context,
            human_review_required=human_review_required,
            human_review_reasons=human_review_reasons,
            evidence=all_evidence
        )


risk_engine = EvidenceRiskEngine()
