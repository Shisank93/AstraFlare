"""
AstraFlare Evidence-Based Thermal Anomaly Risk Engine — Data Quality Evaluator.
Evaluates telemetry completeness, sensor coverage, historical baseline status,
and GIS data quality.
"""
from typing import Tuple, List
from backend.risk_engine.config import RiskEngineConfig
from backend.risk_engine.models import RiskInput, EvidenceItem


def evaluate_data_quality(inp: RiskInput, cfg: RiskEngineConfig) -> Tuple[float, str, List[EvidenceItem]]:
    """
    Evaluates Telemetry & GIS Data Quality Score in [0.0, 1.0] and quality status.
    Quality Status: HIGH (>=0.75), MEDIUM (0.50-0.74), LOW (0.30-0.49), INSUFFICIENT (<0.30).
    """
    evidence = []
    
    # 1. Observation Count & Satellite Sensor Coverage
    obs_cnt = int(inp.observation_count or 1)
    sat_cnt = int(inp.satellite_count or 1)
    conf_ratio = float(inp.confidence_high_ratio or 0.0)

    obs_norm = min(1.0, obs_cnt / 3.0)
    sat_norm = min(1.0, sat_cnt / 2.0)

    # 2. Historical Baseline Quality
    hist_status = str(inp.history_status or "NO_PRIOR_HISTORY")
    if hist_status == "ADEQUATE_HISTORY":
        hist_q = 1.0
    elif hist_status == "LIMITED_HISTORY":
        hist_q = 0.60
    else:
        hist_q = 0.40

    # 3. Composite Data Quality Score
    quality_norm = (obs_norm * 0.35) + (sat_norm * 0.25) + (conf_ratio * 0.20) + (hist_q * 0.20)
    quality_norm = round(min(1.0, max(0.0, quality_norm)), 4)

    if quality_norm >= 0.75:
        status = "HIGH"
        reason = f"High telemetry quality: {sat_cnt} sensor(s), {obs_cnt} observation(s), baseline {hist_status}."
    elif quality_norm >= 0.50:
        status = "MEDIUM"
        reason = f"Moderate telemetry quality: {obs_cnt} observation(s), baseline {hist_status}."
    elif quality_norm >= 0.30:
        status = "LOW"
        reason = f"Low telemetry quality: singleton observation ({obs_cnt}), baseline {hist_status}."
    else:
        status = "INSUFFICIENT"
        reason = "Insufficient telemetry/GIS quality for high-confidence operational routing."

    contrib = quality_norm * cfg.quality_weight
    evidence.append(EvidenceItem(
        type="DATA_QUALITY",
        strength=status,
        value=f"Score: {quality_norm:.2f} ({status})",
        reason=reason,
        input_feature="observation_count",
        input_value=obs_cnt,
        normalization=quality_norm,
        weight=round(cfg.quality_weight, 4),
        contribution=round(contrib, 4)
    ))

    return quality_norm, status, evidence
