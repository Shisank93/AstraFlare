"""
AstraFlare Evidence-Based Thermal Anomaly Risk Engine — Dimensional Scoring Functions.
Computes deterministic, operational evidence scores in [0.0, 1.0] across all 6 evidence dimensions.
"""
import math
from typing import Tuple, List, Dict, Any
from backend.risk_engine.config import RiskEngineConfig
from backend.risk_engine.models import RiskInput, EvidenceItem


def score_thermal_intensity(inp: RiskInput, cfg: RiskEngineConfig) -> Tuple[float, List[EvidenceItem]]:
    """
    Computes Thermal Intensity Evidence Score in [0.0, 1.0].
    Normalizes max_frp, max_brightness, and confidence_high_ratio.
    """
    evidence = []
    
    # 1. FRP Magnitude Component (0.70 weight in thermal dimension)
    frp_val = max(0.0, float(inp.max_frp))
    frp_norm = min(1.0, frp_val / cfg.frp_extreme)
    
    frp_strength = "LOW"
    if frp_val >= cfg.frp_extreme:
        frp_strength = "VERY_HIGH"
    elif frp_val >= cfg.frp_high:
        frp_strength = "HIGH"
    elif frp_val >= cfg.frp_moderate:
        frp_strength = "MODERATE"

    contrib_frp = frp_norm * (cfg.thermal_weight * 0.70)
    evidence.append(EvidenceItem(
        type="THERMAL_ANOMALY",
        strength=frp_strength,
        value=f"{frp_val:.2f} MW",
        reason=f"Peak Fire Radiative Power is {frp_val:.2f} MW ({frp_strength} intensity).",
        input_feature="max_frp",
        input_value=frp_val,
        normalization=round(frp_norm, 4),
        weight=round(cfg.thermal_weight * 0.70, 4),
        contribution=round(contrib_frp, 4)
    ))

    # 2. Brightness Temperature Component (0.20 weight in thermal dimension)
    bright_val = float(inp.max_brightness) if inp.max_brightness is not None else 300.0
    bright_norm = min(1.0, max(0.0, (bright_val - 300.0) / 100.0))
    contrib_bright = bright_norm * (cfg.thermal_weight * 0.20)
    
    if bright_norm > 0.1:
        evidence.append(EvidenceItem(
            type="SATELLITE_RADIANCE",
            strength="HIGH" if bright_norm >= 0.6 else "MODERATE",
            value=f"{bright_val:.1f} K",
            reason=f"Satellite channel brightness temperature recorded at {bright_val:.1f} K.",
            input_feature="max_brightness",
            input_value=bright_val,
            normalization=round(bright_norm, 4),
            weight=round(cfg.thermal_weight * 0.20, 4),
            contribution=round(contrib_bright, 4)
        ))

    # 3. High Confidence Ratio Component (0.10 weight in thermal dimension)
    conf_ratio = min(1.0, max(0.0, float(inp.confidence_high_ratio)))
    contrib_conf = conf_ratio * (cfg.thermal_weight * 0.10)

    thermal_score = min(1.0, max(0.0, frp_norm * 0.70 + bright_norm * 0.20 + conf_ratio * 0.10))
    return round(thermal_score, 4), evidence


def score_historical_anomaly(inp: RiskInput, cfg: RiskEngineConfig) -> Tuple[float, str, List[EvidenceItem]]:
    """
    Computes Historical FRP Anomaly Evidence Score in [0.0, 1.0] and history_status.
    Categorizes Z-score into LOW (<1σ), MODERATE (1-2σ), HIGH (2-3σ), VERY_HIGH (>3σ).
    Handles missing/no history without setting risk to 0 automatically.
    """
    evidence = []
    
    prev_cnt = int(inp.previous_detection_count or 0)
    zscore = inp.frp_anomaly_z

    if zscore is None:
        if prev_cnt == 0:
            history_status = "NO_PRIOR_HISTORY"
            hist_norm = 0.50  # Neutral 0.50 score for unknown baseline
            reason = "No prior satellite thermal history in cell. Baseline unestablished."
        else:
            history_status = "LIMITED_HISTORY"
            hist_norm = 0.40
            reason = "Insufficient historical observations for robust Z-score calculation."
        z_val = 0.0
        z_strength = "LOW"
    else:
        history_status = "ADEQUATE_HISTORY"
        z_val = float(zscore)
        if z_val >= 3.0:
            hist_norm = 1.0
            z_strength = "VERY_HIGH"
        elif z_val >= 2.0:
            hist_norm = 0.75
            z_strength = "HIGH"
        elif z_val >= 1.0:
            hist_norm = 0.50
            z_strength = "MODERATE"
        elif z_val >= 0.0:
            hist_norm = 0.25
            z_strength = "LOW"
        else:
            hist_norm = 0.10
            z_strength = "LOW"

        reason = f"Thermal intensity Z-score is Z={z_val:+.2f} relative to historical baseline ({z_strength} anomaly)."

    contrib = hist_norm * cfg.historical_weight
    evidence.append(EvidenceItem(
        type="HISTORICAL_ANOMALY",
        strength=z_strength if zscore is not None else "MODERATE",
        value=f"Z={z_val:+.2f}" if zscore is not None else history_status,
        reason=reason,
        input_feature="frp_anomaly_z",
        input_value=z_val if zscore is not None else None,
        normalization=round(hist_norm, 4),
        weight=round(cfg.historical_weight, 4),
        contribution=round(contrib, 4)
    ))

    return round(hist_norm, 4), history_status, evidence


def score_industrial_proximity(inp: RiskInput, cfg: RiskEngineConfig) -> Tuple[float, List[EvidenceItem]]:
    """
    Computes Industrial Proximity Evidence Score in [0.0, 1.0].
    Distance <= 250m -> 1.0, <= 1000m -> 0.80, <= 5000m -> 0.40, > 5000m -> 0.0.
    """
    evidence = []
    dist_m = max(0.0, float(inp.industrial_distance_m or 10000.0))

    if dist_m <= cfg.dist_immediate_m:
        prox_norm = 1.0
        prox_strength = "VERY_HIGH"
        reason = f"Thermal event centroid is within immediate industrial boundary ({dist_m:.1f}m <= 250m)."
    elif dist_m <= cfg.dist_close_m:
        # Linear interpolation between 250m and 1000m -> [1.0, 0.75]
        prox_norm = 1.0 - 0.25 * ((dist_m - 250.0) / 750.0)
        prox_strength = "HIGH"
        reason = f"Thermal event centroid is located in close industrial perimeter ({dist_m:.1f}m <= 1000m)."
    elif dist_m <= cfg.dist_moderate_m:
        # Linear interpolation between 1000m and 5000m -> [0.75, 0.15]
        prox_norm = 0.75 - 0.60 * ((dist_m - 1000.0) / 4000.0)
        prox_strength = "MODERATE"
        reason = f"Thermal event centroid is located within regional industrial vicinity ({dist_m:.1f}m <= 5000m)."
    else:
        prox_norm = 0.0
        prox_strength = "LOW"
        reason = f"Thermal event centroid is spatially remote from industrial infrastructure ({dist_m:.1f}m > 5000m)."

    contrib = prox_norm * (cfg.industrial_weight * 0.70)
    evidence.append(EvidenceItem(
        type="INDUSTRIAL_PROXIMITY",
        strength=prox_strength,
        value=f"{dist_m:.1f} meters",
        reason=reason,
        input_feature="industrial_distance_m",
        input_value=dist_m,
        normalization=round(prox_norm, 4),
        weight=round(cfg.industrial_weight * 0.70, 4),
        contribution=round(contrib, 4)
    ))

    return round(prox_norm, 4), evidence


def score_industrial_density(inp: RiskInput, cfg: RiskEngineConfig) -> Tuple[float, List[EvidenceItem]]:
    """
    Computes Industrial Site Density Context Score in [0.0, 1.0].
    Evaluates site counts within 250m, 1km, 5km to avoid excessive double counting with distance.
    """
    evidence = []
    cnt_250m = int(inp.industrial_site_count_250m or 0)
    cnt_1km = int(inp.industrial_site_count_1km or 0)
    cnt_5km = int(inp.industrial_site_count_5km or 0)

    # Weighted site density combination
    density_raw = cnt_250m * 0.50 + cnt_1km * 0.30 + cnt_5km * 0.20
    density_norm = min(1.0, max(0.0, density_raw / 5.0))

    if density_norm > 0:
        contrib = density_norm * (cfg.industrial_weight * 0.30)
        evidence.append(EvidenceItem(
            type="INDUSTRIAL_DENSITY",
            strength="HIGH" if density_norm >= 0.5 else "MODERATE",
            value=f"{cnt_1km} sites (1km), {cnt_5km} sites (5km)",
            reason=f"Spatial industrial site density around event centroid includes {cnt_1km} sites within 1km and {cnt_5km} within 5km.",
            input_feature="industrial_site_count_1km",
            input_value=cnt_1km,
            normalization=round(density_norm, 4),
            weight=round(cfg.industrial_weight * 0.30, 4),
            contribution=round(contrib, 4)
        ))

    return round(density_norm, 4), evidence


def score_natural_context(inp: RiskInput, cfg: RiskEngineConfig) -> Tuple[float, str, List[EvidenceItem]]:
    """
    Computes Natural / Wildland Land Cover Evidence Score in [0.0, 1.0] and land_cover_interpretation.
    Trees / Forest -> High natural fire context.
    Built-up / Industrial -> Low natural fire context.
    """
    evidence = []
    wc_str = str(inp.worldcover_class or "Unknown").lower()

    if "tree" in wc_str or "forest" in wc_str or "10" in wc_str:
        nat_norm = 1.0
        interp = "TREE_COVER_FOREST"
        strength = "HIGH"
        reason = f"ESA 10m WorldCover classifies surface as '{inp.worldcover_class}' (high wildland vegetation)."
    elif "shrub" in wc_str or "grass" in wc_str or "20" in wc_str or "30" in wc_str:
        nat_norm = 0.70
        interp = "SHRUBLAND_GRASSLAND"
        strength = "MODERATE"
        reason = f"ESA 10m WorldCover classifies surface as '{inp.worldcover_class}' (moderate vegetation)."
    elif "crop" in wc_str or "agri" in wc_str or "40" in wc_str:
        nat_norm = 0.40
        interp = "AGRICULTURAL_CROPLAND"
        strength = "MODERATE"
        reason = f"ESA 10m WorldCover classifies surface as '{inp.worldcover_class}' (agricultural cropland)."
    elif "built" in wc_str or "urban" in wc_str or "50" in wc_str:
        nat_norm = 0.0
        interp = "BUILT_UP_INDUSTRIAL"
        strength = "LOW"
        reason = f"ESA 10m WorldCover classifies surface as '{inp.worldcover_class}' (urban/industrial built-up)."
    else:
        nat_norm = 0.20
        interp = "OTHER_LAND_COVER"
        strength = "LOW"
        reason = f"ESA 10m WorldCover surface land use: '{inp.worldcover_class}'."

    contrib = nat_norm * cfg.natural_weight
    evidence.append(EvidenceItem(
        type="LAND_COVER",
        strength=strength,
        value=str(inp.worldcover_class),
        reason=reason,
        input_feature="worldcover_class",
        input_value=inp.worldcover_class,
        normalization=round(nat_norm, 4),
        weight=round(cfg.natural_weight, 4),
        contribution=round(contrib, 4)
    ))

    return round(nat_norm, 4), interp, evidence


def score_recurrence_and_persistence(inp: RiskInput, cfg: RiskEngineConfig) -> Tuple[float, float, List[EvidenceItem]]:
    """
    Computes Recurrence Score [0.0, 1.0] and Persistence Score [0.0, 1.0].
    Distinguishes PERSISTENT_ACTIVITY (frequent historical activity + stable FRP)
    from UNUSUAL_ACTIVITY (rare history + strong current anomaly).
    """
    evidence = []
    
    prev_cnt = int(inp.previous_detection_count or 0)
    dur_h = float(inp.duration_hours or 0.0)
    obs_cnt = int(inp.observation_count or 1)

    # 1. Recurrence Score (Historical repetition in cell)
    rec_norm = min(1.0, max(0.0, prev_cnt / 10.0))

    # 2. Persistence Score (Current cluster duration & multi-observation density)
    pers_norm = min(1.0, max(0.0, (dur_h / 24.0) * 0.50 + (obs_cnt / 5.0) * 0.50))

    if prev_cnt >= 5:
        reason = f"Cell exhibits frequent historical recurrence ({prev_cnt} prior detections)."
        strength = "HIGH"
    elif prev_cnt >= 2:
        reason = f"Cell exhibits moderate historical recurrence ({prev_cnt} prior detections)."
        strength = "MODERATE"
    else:
        reason = f"Cell exhibits rare historical recurrence ({prev_cnt} prior detections)."
        strength = "LOW"

    contrib = rec_norm * cfg.recurrence_weight
    evidence.append(EvidenceItem(
        type="HISTORICAL_RECURRENCE",
        strength=strength,
        value=f"{prev_cnt} prior detections, {dur_h:.1f}h duration",
        reason=reason,
        input_feature="previous_detection_count",
        input_value=prev_cnt,
        normalization=round(rec_norm, 4),
        weight=round(cfg.recurrence_weight, 4),
        contribution=round(contrib, 4)
    ))

    return round(rec_norm, 4), round(pers_norm, 4), evidence
