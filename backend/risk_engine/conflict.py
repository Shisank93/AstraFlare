"""
AstraFlare Evidence-Based Thermal Anomaly Risk Engine — Conflict Detector & Context Resolver.
Detects conflicting GIS/thermal evidence signals and evaluates operational human review routing.
"""
from typing import Tuple, List, Dict, Any
from backend.risk_engine.config import RiskEngineConfig
from backend.risk_engine.models import RiskInput


def evaluate_evidence_conflict_and_context(
    inp: RiskInput,
    ind_prox_score: float,
    ind_dens_score: float,
    nat_score: float,
    hist_anomaly_score: float,
    rec_score: float,
    pers_score: float,
    quality_score: float,
    quality_status: str,
    overall_risk_score: float,
    cfg: RiskEngineConfig
) -> Tuple[str, str, bool, List[str]]:
    """
    Evaluates evidence_status, likely_context, human_review_required, and human_review_reasons.
    
    Status Values:
    - CONFLICTING_EVIDENCE
    - STRONG_INDUSTRIAL_CONTEXT
    - STRONG_NATURAL_CONTEXT
    - PERSISTENT_INDUSTRIAL_CONTEXT
    - UNUSUAL_THERMAL_ACTIVITY
    - INSUFFICIENT_EVIDENCE
    
    Likely Context Values:
    - INDUSTRIAL_CONTEXT
    - NATURAL_FIRE_CONTEXT
    - PERSISTENT_INDUSTRIAL_CONTEXT
    - AMBIGUOUS
    """
    reasons: List[str] = []
    is_conflicting = False

    dist_m = float(inp.industrial_distance_m or 10000.0)
    frp_val = float(inp.max_frp or 0.0)
    prev_cnt = int(inp.previous_detection_count or 0)

    # 1. Detect Conflict between Industrial Proximity & Forest/Vegetation Land Cover
    if dist_m <= cfg.dist_close_m and nat_score >= 0.70 and frp_val >= cfg.frp_high:
        is_conflicting = True
        reasons.append(
            f"Evidence Conflict: Event is in close industrial proximity ({dist_m:.0f}m) "
            f"yet located on dense natural vegetation land cover ({inp.worldcover_class}) with high FRP ({frp_val:.1f} MW)."
        )

    # 2. Determine Evidence Status and Likely Context
    if is_conflicting:
        evidence_status = "CONFLICTING_EVIDENCE"
        likely_context = "AMBIGUOUS"
    elif quality_status == "INSUFFICIENT" or (quality_score < 0.30 and frp_val < cfg.frp_moderate):
        evidence_status = "INSUFFICIENT_EVIDENCE"
        likely_context = "AMBIGUOUS"
        reasons.append("Insufficient data quality and thermal telemetry for high-confidence context attribution.")
    elif ind_prox_score >= 0.75 and rec_score >= 0.50 and frp_val < cfg.frp_extreme:
        evidence_status = "PERSISTENT_INDUSTRIAL_CONTEXT"
        likely_context = "PERSISTENT_INDUSTRIAL_CONTEXT"
    elif ind_prox_score >= 0.75:
        evidence_status = "STRONG_INDUSTRIAL_CONTEXT"
        likely_context = "INDUSTRIAL_CONTEXT"
    elif nat_score >= 0.70 and ind_prox_score < 0.25:
        evidence_status = "STRONG_NATURAL_CONTEXT"
        likely_context = "NATURAL_FIRE_CONTEXT"
    elif hist_anomaly_score >= 0.75 or frp_val >= cfg.frp_extreme:
        evidence_status = "UNUSUAL_THERMAL_ACTIVITY"
        if ind_prox_score >= 0.40:
            likely_context = "INDUSTRIAL_CONTEXT"
        elif nat_score >= 0.40:
            likely_context = "NATURAL_FIRE_CONTEXT"
        else:
            likely_context = "AMBIGUOUS"
    else:
        evidence_status = "INSUFFICIENT_EVIDENCE"
        likely_context = "AMBIGUOUS"

    # 3. Human Review Gate Evaluation
    human_review_required = False

    if is_conflicting:
        human_review_required = True
    elif evidence_status == "INSUFFICIENT_EVIDENCE":
        human_review_required = True
        reasons.append("Insufficient evidence quality requires analyst review.")
    elif quality_status in ("LOW", "INSUFFICIENT"):
        human_review_required = True
        reasons.append(f"Telemetry quality is {quality_status}; manual analyst verification recommended.")
    elif ind_prox_score >= 0.75 and frp_val >= cfg.frp_high and prev_cnt <= 2:
        # High FRP thermal event near industrial facility with low/no prior recurrence
        human_review_required = True
        reasons.append(f"High-intensity thermal anomaly near industrial site ({frp_val:.1f} MW at {dist_m:.0f}m) with low prior recurrence ({prev_cnt}).")
    elif overall_risk_score >= cfg.risk_review_threshold:
        if likely_context == "AMBIGUOUS":
            human_review_required = True
            reasons.append(f"High risk score ({overall_risk_score:.2f} >= {cfg.risk_review_threshold:.2f}) with ambiguous context.")
        elif ind_prox_score >= 0.75 and frp_val >= cfg.frp_high and rec_score < 0.50:
            # Unusual high FRP near industry (potential industrial incident)
            human_review_required = True
            reasons.append(f"High risk potential industrial anomaly ({frp_val:.1f} MW near industry, low historical recurrence).")

    return evidence_status, likely_context, human_review_required, reasons
