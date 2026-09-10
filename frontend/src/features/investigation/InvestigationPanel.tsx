import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  ShieldAlert,
  MapPin,
  Flame,
  Send,
  FileText,
  Brain,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Info,
  Clock,
  ShieldCheck,
  Building2
} from 'lucide-react';
import { api } from '../../api/client';
import type {
  HotspotDetail,
  PredictionResponse,
  EvidenceResponse,
  RiskResponse,
  HistoryResponse,
  ReviewDecision,
  ClassificationType,
} from '../../types/api';
import { Badge } from '../../components/common/Badge';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ErrorState } from '../../components/common/ErrorState';

interface InvestigationPanelProps {
  hotspotId: string | null;
  onReviewSubmitted?: () => void;
  onGenerateReport?: (hotspotId: string) => void;
}

export const InvestigationPanel: React.FC<InvestigationPanelProps> = ({
  hotspotId,
  onReviewSubmitted,
  onGenerateReport,
}) => {
  const [detail, setDetail] = useState<HotspotDetail | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [evidence, setEvidence] = useState<EvidenceResponse | null>(null);
  const [risk, setRisk] = useState<RiskResponse | null>(null);
  const [history, setHistory] = useState<HistoryResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showModelCard, setShowModelCard] = useState<boolean>(false);

  // Review Form State
  const [reviewerId, setReviewerId] = useState<string>('ANALYST-01');
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [selectedCorrectedClass, setSelectedCorrectedClass] = useState<ClassificationType | ''>('');
  const [submittingReview, setSubmittingReview] = useState<boolean>(false);
  const [reviewSuccessMsg, setReviewSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!hotspotId) {
      setDetail(null);
      setPrediction(null);
      setEvidence(null);
      setRisk(null);
      setHistory(null);
      setError(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);
    setReviewSuccessMsg(null);

    Promise.all([
      api.getHotspotDetail(hotspotId),
      api.getHotspotPrediction(hotspotId),
      api.getHotspotEvidence(hotspotId),
      api.getHotspotRisk(hotspotId),
      api.getHotspotHistory(hotspotId),
    ])
      .then(([det, pred, ev, rk, hist]) => {
        if (!isMounted) return;
        setDetail(det);
        setPrediction(pred);
        setEvidence(ev);
        setRisk(rk);
        setHistory(hist);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to load hotspot investigation details.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [hotspotId]);

  const handleSubmitReview = async (decision: ReviewDecision) => {
    if (!hotspotId) return;
    setSubmittingReview(true);
    setReviewSuccessMsg(null);

    try {
      const res = await api.submitReview(hotspotId, {
        decision,
        reviewer_id: reviewerId || 'ANALYST-01',
        notes: reviewNotes,
        corrected_classification: decision === 'CORRECTED' && selectedCorrectedClass ? selectedCorrectedClass : undefined,
      });

      setReviewSuccessMsg(`Review successfully recorded: ${res.review_status}`);
      setDetail((prev) => (prev ? { ...prev, review_status: res.review_status } : prev));
      if (onReviewSubmitted) onReviewSubmitted();
    } catch (err: any) {
      alert(`Failed to submit review: ${err.message}`);
    } finally {
      setSubmittingReview(false);
    }
  };

  if (!hotspotId) {
    return (
      <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <MapPin size={32} style={{ marginBottom: '8px', opacity: 0.4 }} />
        <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>No Hotspot Selected</div>
        <div style={{ fontSize: '12px', marginTop: '4px' }}>
          Select an observation marker on the map or choose an alert item from the queue to investigate.
        </div>
      </div>
    );
  }

  if (loading) {
    return <LoadingSpinner message={`Fetching investigation telemetry for ${hotspotId}...`} />;
  }

  if (error || !detail) {
    return <ErrorState message={error || 'Hotspot data not available.'} />;
  }

  // Industrial distance formatting
  const distM = detail.industrial_distance_m != null ? detail.industrial_distance_m : 10000;
  const distStr = distM >= 1000 ? `${(distM / 1000).toFixed(1)} km` : `${distM.toFixed(0)} m`;
  const isNearIndustry = distM <= 3000;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Investigation Header */}
      <div className="panel-header" style={{ backgroundColor: '#0f172a', color: '#ffffff', padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#38bdf8', fontWeight: 700 }}>
            EVENT INVESTIGATION DOSSIER
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, fontFamily: 'monospace', color: '#f8fafc' }}>
            {detail.id}
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {onGenerateReport && (
            <button
              onClick={() => onGenerateReport(detail.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 8px',
                fontSize: '11px',
                fontWeight: 600,
                backgroundColor: '#1e293b',
                color: '#38bdf8',
                border: '1px solid #334155',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              <FileText size={12} /> Dossier
            </button>
          )}
          <Badge riskLevel={detail.risk_level} />
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        
        {/* 1. Observation Telemetry Summary */}
        <div style={{ backgroundColor: '#ffffff', padding: '12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', justifyContent: 'space-between' }}>
            <span>Satellite Telemetry</span>
            <span style={{ color: '#0f172a', fontWeight: 600 }}>{detail.data_source}</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
            <div>
              <span style={{ fontSize: '10px', color: '#64748b', display: 'block' }}>Acquisition Time</span>
              <span style={{ fontWeight: 600, color: '#0f172a' }}>
                {detail.acq_timestamp?.split('T')[0]} {detail.acq_timestamp?.split('T')[1]?.substring(0, 5)}
              </span>
            </div>
            <div>
              <span style={{ fontSize: '10px', color: '#64748b', display: 'block' }}>FRP / Intensity</span>
              <span style={{ fontWeight: 700, color: '#ea580c' }}>
                <Flame size={12} style={{ display: 'inline', marginRight: '2px' }} />
                {detail.frp?.toFixed(1)} MW
              </span>
            </div>
            <div>
              <span style={{ fontSize: '10px', color: '#64748b', display: 'block' }}>Coordinates</span>
              <span style={{ fontWeight: 600, color: '#0f172a' }}>
                {detail.latitude?.toFixed(4)}°, {detail.longitude?.toFixed(4)}°
              </span>
            </div>
            <div>
              <span style={{ fontSize: '10px', color: '#64748b', display: 'block' }}>Satellite</span>
              <span style={{ fontWeight: 600, color: '#0f172a' }}>
                {detail.satellite}
              </span>
            </div>
          </div>
        </div>

        {/* 2. ML Classification & Calibrated Probability */}
        {prediction && (
          <div style={{ backgroundColor: '#ffffff', padding: '14px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '5px' }}>
                <Brain size={14} color="#2563eb" /> ML Classification Prediction
              </span>
              <span
                style={{
                  padding: '2px 7px',
                  fontSize: '9px',
                  fontWeight: 700,
                  backgroundColor: '#e0e7ff',
                  color: '#3730a3',
                  borderRadius: '3px',
                  letterSpacing: '0.04em',
                }}
              >
                RESEARCH BASELINE
              </span>
            </div>

            {/* Prediction & Confidence Block */}
            <div style={{ padding: '10px', backgroundColor: '#f8fafc', borderRadius: '5px', border: '1px solid #e2e8f0', marginBottom: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>
                  Predicted Category
                </span>
                <span
                  style={{
                    padding: '2px 6px',
                    fontSize: '10px',
                    fontWeight: 700,
                    borderRadius: '3px',
                    backgroundColor:
                      prediction.confidence_status === 'HIGH CONFIDENCE'
                        ? '#dcfce7'
                        : prediction.confidence_status === 'MODERATE CONFIDENCE'
                        ? '#dbeafe'
                        : '#fef3c7',
                    color:
                      prediction.confidence_status === 'HIGH CONFIDENCE'
                        ? '#15803d'
                        : prediction.confidence_status === 'MODERATE CONFIDENCE'
                        ? '#1d4ed8'
                        : '#b45309',
                  }}
                >
                  {prediction.confidence_status || (prediction.review_required ? 'LOW CONFIDENCE — ANALYST REVIEW' : 'HIGH CONFIDENCE')}
                </span>
              </div>

              <div style={{ fontSize: '14px', fontWeight: 800, color: '#0f172a' }}>
                {prediction.predicted_class ? prediction.predicted_class.replace(/_/g, ' ') : 'UNLABELED'}
              </div>

              <div style={{ fontSize: '11px', color: '#2563eb', fontWeight: 700, marginTop: '2px' }}>
                Calibrated Confidence: {prediction.confidence != null ? `${(prediction.confidence * 100).toFixed(1)}%` : 'N/A'}
              </div>

              {prediction.abstention_reason && (
                <div style={{ fontSize: '10px', color: '#64748b', fontStyle: 'italic', marginTop: '4px' }}>
                  {prediction.abstention_reason}
                </div>
              )}
            </div>

            {/* Calibrated Probability Distribution */}
            {prediction.probabilities && (
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '10px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Probability Distribution
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {Object.entries(prediction.probabilities).map(([cls, prob]: [string, any]) => (
                    <div key={cls}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '2px' }}>
                        <span style={{ color: '#334155', fontWeight: 500 }}>{cls.replace(/_/g, ' ')}</span>
                        <span style={{ fontWeight: 700, color: cls === prediction.predicted_class ? '#2563eb' : '#64748b' }}>
                          {(Number(prob) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div style={{ height: '6px', backgroundColor: '#f1f5f9', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${Number(prob) * 100}%`,
                            height: '100%',
                            backgroundColor: cls === prediction.predicted_class ? '#2563eb' : '#cbd5e1',
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Why this prediction? TreeSHAP / Explanations */}
            {prediction.top_contributing_features && prediction.top_contributing_features.length > 0 && (
              <div style={{ padding: '10px', backgroundColor: '#f8fafc', borderRadius: '5px', border: '1px solid #e2e8f0', marginBottom: '10px' }}>
                <div style={{ fontSize: '10px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '4px' }}>
                  Why This Prediction? (Top Features)
                </div>
                <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '11px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                  {prediction.top_contributing_features.slice(0, 3).map((f: any, idx: number) => (
                    <li key={idx}>
                      <strong>{f.feature}:</strong> {f.statement || f.value}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Supplementary Industrial Anomaly Assessment Card (Item 12) */}
            {prediction.industrial_anomaly_score != null && (
              <div style={{ padding: '10px', backgroundColor: '#f1f5f9', borderRadius: '5px', border: '1px solid #e2e8f0', marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '10px', fontWeight: 700, color: '#475569', textTransform: 'uppercase' }}>
                    Industrial Anomaly Assessment
                  </span>
                  <span style={{ fontSize: '10px', fontWeight: 700, color: prediction.industrial_anomaly_level === 'HIGH' ? '#dc2626' : '#475569' }}>
                    Tier: {prediction.industrial_anomaly_level || 'LOW'} (Score: {prediction.industrial_anomaly_score.toFixed(3)})
                  </span>
                </div>
                <div style={{ fontSize: '10px', color: '#64748b' }}>
                  Unsupervised multi-factor signal (FRP deviation, recurrence, proximity). Supplementary evidence indicator.
                </div>
              </div>
            )}

            {/* Compact Expandable Research Status Card (Item 14) */}
            <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '8px' }}>
              <button
                onClick={() => setShowModelCard(!showModelCard)}
                style={{
                  width: '100%',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'none',
                  border: 'none',
                  padding: '4px 0',
                  fontSize: '11px',
                  fontWeight: 600,
                  color: '#475569',
                  cursor: 'pointer',
                }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Info size={12} color="#2563eb" /> Model Status & Training Partition Stats
                </span>
                {showModelCard ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              </button>

              {showModelCard && (
                <div style={{ marginTop: '8px', padding: '10px', backgroundColor: '#f8fafc', borderRadius: '5px', border: '1px solid #e2e8f0', fontSize: '11px', color: '#334155' }}>
                  <div style={{ fontWeight: 700, color: '#0f172a', marginBottom: '4px' }}>
                    Research Baseline — Data Limited
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginBottom: '6px' }}>
                    <div>Training: <strong>54,386 rows</strong></div>
                    <div>Test: <strong>14,289 rows</strong></div>
                    <div>Facility Overlap: <strong>0</strong></div>
                    <div>Event Overlap: <strong>0</strong></div>
                    <div>Macro F1: <strong>0.6667</strong></div>
                    <div>Wildland F1: <strong>1.0</strong></div>
                    <div>Persistent Heat F1: <strong>1.0</strong></div>
                    <div>Industrial Incident: <strong>0.0 (Rare Class)</strong></div>
                  </div>
                  <p style={{ margin: 0, fontSize: '10px', lineHeight: '1.4', color: '#64748b', fontStyle: 'italic' }}>
                    The current model demonstrates strong separation for well-represented classes. Industrial incident classification remains data-limited because verified incidents are rare. Predictions should therefore be interpreted with evidence and analyst review.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 3. Operational Prioritization Risk (Decoupled from ML) */}
        {risk && (
          <div style={{ backgroundColor: '#ffffff', padding: '14px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '5px' }}>
                <AlertTriangle size={14} color="#ea580c" /> Operational Prioritization Risk
              </span>
              <Badge riskLevel={risk.risk_level} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '6px' }}>
              <span style={{ fontSize: '11px', color: '#64748b' }}>Queue Risk Score:</span>
              <span style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a' }}>
                {risk.risk_score.toFixed(3)}
              </span>
            </div>

            {risk.contributing_factors && risk.contributing_factors.length > 0 && (
              <div style={{ marginTop: '8px', borderTop: '1px solid #f1f5f9', paddingTop: '8px' }}>
                <span style={{ fontSize: '10px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
                  Contributing Operational Factors
                </span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                  {risk.contributing_factors.map((f, idx) => (
                    <div key={idx} style={{ fontSize: '11px', display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#334155' }}>{f.factor}:</span>
                      <span style={{ fontWeight: 600, color: '#0f172a' }}>{f.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div style={{ fontSize: '10px', color: '#94a3b8', fontStyle: 'italic', marginTop: '6px' }}>
              Operational risk determines queue urgency; it is independent of ML classification.
            </div>
          </div>
        )}

        {/* 4. Multi-Layer Evidence Section */}
        {evidence && (
          <div style={{ backgroundColor: '#ffffff', padding: '14px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#0f172a', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <ShieldCheck size={14} color="#059669" /> Multi-Layer Evidence Synthesis
            </div>

            {/* Industrial Proximity Tile */}
            <div style={{ padding: '8px', backgroundColor: isNearIndustry ? '#fee2e2' : '#f8fafc', borderRadius: '4px', border: `1px solid ${isNearIndustry ? '#fecaca' : '#e2e8f0'}`, marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: 700, color: isNearIndustry ? '#991b1b' : '#334155' }}>
                <Building2 size={13} />
                Industrial Proximity: {distStr} ({isNearIndustry ? 'Near Industry' : 'Low Industrial Proximity'})
              </div>
              <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
                Nearest Site: {detail.nearest_industrial_name || 'No mapped facilities within 5km radius'}
              </div>
            </div>

            {/* Evidence Statements */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {evidence.evidence_items.map((ev, idx) => (
                <div key={idx} style={{ fontSize: '11px', padding: '6px', backgroundColor: '#f8fafc', borderRadius: '4px', border: '1px solid #f1f5f9' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569', fontWeight: 600, marginBottom: '1px' }}>
                    <span>{ev.category?.replace(/_/g, ' ') || ev.evidence_type?.replace(/_/g, ' ')}</span>
                    <span style={{ color: '#0f172a' }}>{ev.value}</span>
                  </div>
                  <div style={{ color: '#64748b', fontSize: '10px' }}>{ev.interpretation}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 5. Historical 30-Day Recurrence Baseline */}
        {history && (
          <div style={{ backgroundColor: '#ffffff', padding: '14px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#0f172a', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Clock size={14} color="#475569" /> Historical Recurrence Baseline
            </div>
            <div style={{ fontSize: '11px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', color: '#334155' }}>
              <div>30-Day Detections: <strong>{history.recurrence_count_30d}</strong></div>
              <div>365-Day Detections: <strong>{history.recurrence_count_365d}</strong></div>
              <div>FRP Anomaly: <strong>{history.frp_anomaly_zscore ? `+${history.frp_anomaly_zscore.toFixed(2)} sigma` : '0.00 sigma'}</strong></div>
              <div>Mean Baseline FRP: <strong>{history.historical_mean_frp ? `${history.historical_mean_frp.toFixed(1)} MW` : 'N/A'}</strong></div>
            </div>
          </div>
        )}

        {/* 6. Human Analyst Review Action Form */}
        <div style={{ backgroundColor: '#ffffff', padding: '14px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
            Analyst Investigation & Decision
          </div>

          {reviewSuccessMsg && (
            <div style={{ padding: '8px', backgroundColor: '#dcfce7', color: '#15803d', borderRadius: '4px', fontSize: '11px', marginBottom: '8px', fontWeight: 600 }}>
              {reviewSuccessMsg}
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div>
              <label style={{ fontSize: '10px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                Analyst ID
              </label>
              <input
                type="text"
                value={reviewerId}
                onChange={(e) => setReviewerId(e.target.value)}
                style={{ width: '100%', padding: '5px 8px', fontSize: '11px', border: '1px solid #cbd5e1', borderRadius: '4px' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '10px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                Investigation Findings / Notes
              </label>
              <textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Record ground truth context, facility details, or escalation reasons..."
                style={{ width: '100%', height: '50px', padding: '5px 8px', fontSize: '11px', border: '1px solid #cbd5e1', borderRadius: '4px', resize: 'vertical' }}
              />
            </div>

            {/* Optional Correction Selector */}
            <div>
              <label style={{ fontSize: '10px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                Corrected Class (If Correcting)
              </label>
              <select
                value={selectedCorrectedClass}
                onChange={(e) => setSelectedCorrectedClass(e.target.value as ClassificationType)}
                style={{ width: '100%', padding: '5px 8px', fontSize: '11px', border: '1px solid #cbd5e1', borderRadius: '4px', backgroundColor: '#ffffff' }}
              >
                <option value="">-- Choose Classification --</option>
                <option value="LIKELY_INDUSTRIAL_INCIDENT">Likely Industrial Incident</option>
                <option value="PERSISTENT_INDUSTRIAL_HEAT">Persistent Industrial Heat</option>
                <option value="NATURAL_WILDLAND_FIRE">Natural Wildland Fire</option>
              </select>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginTop: '4px' }}>
              <button
                onClick={() => handleSubmitReview('CONFIRMED')}
                disabled={submittingReview}
                style={{ padding: '6px', fontSize: '11px', fontWeight: 700, backgroundColor: '#15803d', color: '#ffffff', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
              >
                <CheckCircle2 size={12} /> Confirm
              </button>
              <button
                onClick={() => handleSubmitReview('REJECTED')}
                disabled={submittingReview}
                style={{ padding: '6px', fontSize: '11px', fontWeight: 700, backgroundColor: '#dc2626', color: '#ffffff', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
              >
                <XCircle size={12} /> Reject
              </button>
              <button
                onClick={() => handleSubmitReview('ESCALATED')}
                disabled={submittingReview}
                style={{ padding: '6px', fontSize: '11px', fontWeight: 700, backgroundColor: '#d97706', color: '#ffffff', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
              >
                <ShieldAlert size={12} /> Escalate
              </button>
              <button
                onClick={() => handleSubmitReview('CORRECTED')}
                disabled={submittingReview || !selectedCorrectedClass}
                style={{ padding: '6px', fontSize: '11px', fontWeight: 700, backgroundColor: '#2563eb', color: '#ffffff', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
              >
                <Send size={12} /> Correct
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
