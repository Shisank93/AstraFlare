import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  ShieldAlert,
  MapPin,
  Flame,
  Send,
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
import { Button } from '../../components/common/Button';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ErrorState } from '../../components/common/ErrorState';

interface InvestigationPanelProps {
  hotspotId: string | null;
  onReviewSubmitted?: () => void;
}

export const InvestigationPanel: React.FC<InvestigationPanelProps> = ({
  hotspotId,
  onReviewSubmitted,
}) => {
  const [detail, setDetail] = useState<HotspotDetail | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [evidence, setEvidence] = useState<EvidenceResponse | null>(null);
  const [risk, setRisk] = useState<RiskResponse | null>(null);
  const [history, setHistory] = useState<HistoryResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Investigation Header */}
      <div className="panel-header" style={{ backgroundColor: 'var(--accent-navy)', color: '#ffffff' }}>
        <div>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#93c5fd' }}>
            Selected Hotspot Investigation
          </div>
          <div style={{ fontSize: '15px', fontWeight: 700 }}>{detail.id}</div>
        </div>
        <div style={{ display: 'flex', gap: '6px' }}>
          <Badge riskLevel={detail.risk_level} />
          {detail.review_required && <Badge reviewRequired={true} text="REVIEW REQUIRED" />}
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {/* 1. Observation Telemetry Summary */}
        <div className="detail-section">
          <div className="detail-header">
            <span>Satellite Observation Telemetry</span>
            <span className="badge badge-neutral">{detail.data_source}</span>
          </div>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-item-label">Acquisition Time</span>
              <span className="info-item-value">
                {new Date(detail.acq_timestamp).toLocaleDateString()} {new Date(detail.acq_timestamp).toLocaleTimeString()}
              </span>
            </div>
            <div className="info-item">
              <span className="info-item-label">Satellite Sensor</span>
              <span className="info-item-value">{detail.satellite} {detail.instrument ? `(${detail.instrument})` : ''}</span>
            </div>
            <div className="info-item">
              <span className="info-item-label">Fire Radiative Power</span>
              <span className="info-item-value" style={{ color: '#dc2626' }}>
                <Flame size={13} style={{ display: 'inline', marginRight: '3px' }} />
                {detail.frp} MW
              </span>
            </div>
            <div className="info-item">
              <span className="info-item-label">Coordinates (WGS84)</span>
              <span className="info-item-value" style={{ fontSize: '12px' }}>
                {detail.latitude.toFixed(4)}°, {detail.longitude.toFixed(4)}°
              </span>
            </div>
            {detail.brightness && (
              <div className="info-item">
                <span className="info-item-label">Brightness Temp</span>
                <span className="info-item-value">{detail.brightness} K</span>
              </div>
            )}
            {detail.confidence && (
              <div className="info-item">
                <span className="info-item-label">FIRMS Confidence</span>
                <span className="info-item-value">{detail.confidence}</span>
              </div>
            )}
          </div>
        </div>

        {/* 2. Classification & Model Predictions */}
        {prediction && (
          <div className="detail-section">
            <div className="detail-header">
              <span>ML Classification Prediction</span>
              <span className="badge badge-neutral" style={{ fontWeight: 700, backgroundColor: '#e0e7ff', color: '#3730a3' }}>
                {prediction.model_status}
              </span>
            </div>

            {!prediction.is_ml_prediction ? (
              <div style={{ marginBottom: '12px', padding: '16px', backgroundColor: 'var(--bg-surface-subtle)', borderRadius: '6px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)' }}>
                  ML Prediction Unavailable
                </div>
                {prediction.reference_label && (
                  <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-color)', textAlign: 'left' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Reference Label</span>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                      {prediction.reference_label.replace(/_/g, ' ')}
                    </div>
                    {prediction.reference_provenance && (
                      <span className="badge badge-neutral" style={{ fontSize: '10px', marginTop: '4px' }}>
                        Provenance: {prediction.reference_provenance}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <>
                <div style={{ marginBottom: '12px', padding: '10px 12px', backgroundColor: 'var(--bg-surface-subtle)', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Predicted Class</span>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-blue)' }}>
                      Confidence: {prediction.confidence != null ? (prediction.confidence * 100).toFixed(1) : 0}%
                    </span>
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {prediction.predicted_class ? prediction.predicted_class.replace(/_/g, ' ') : 'UNAVAILABLE'}
                  </div>
                </div>

                {/* Probability Breakdown */}
                {prediction.probabilities && (
                  <div style={{ marginTop: '8px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                      Class Probability Distribution
                    </div>
                    {Object.entries(prediction.probabilities).map(([clsName, prob]) => (
                      <div key={clsName} className="prob-bar-container">
                        <div className="prob-label-row">
                          <span>{clsName.replace(/_/g, ' ')}</span>
                          <span style={{ fontWeight: 600 }}>{(Number(prob) * 100).toFixed(1)}%</span>
                        </div>
                        <div className="prob-bar-track">
                          <div
                            className="prob-bar-fill"
                            style={{
                              width: `${Number(prob) * 100}%`,
                              backgroundColor: clsName === prediction.predicted_class ? 'var(--accent-blue)' : '#cbd5e1',
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: '8px' }}>
              {prediction.limitations}
            </div>
          </div>
        )}

        {/* 3. Operational Risk Score */}
        {risk && (
          <div className="detail-section">
            <div className="detail-header">
              <span>Operational Prioritization Risk</span>
              <Badge riskLevel={risk.risk_level} />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', backgroundColor: 'var(--bg-surface-subtle)', borderRadius: '6px', marginBottom: '12px' }}>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Prioritization Score</div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: risk.risk_level === 'HIGH' ? '#dc2626' : risk.risk_level === 'MEDIUM' ? '#d97706' : '#16a34a' }}>
                  {risk.risk_score.toFixed(2)} / 1.00
                </div>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', maxWidth: '200px', textAlign: 'right' }}>
                {risk.explanation}
              </div>
            </div>

            {/* Factor breakdown */}
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
              Contributing Risk Factors
            </div>
            {risk.contributing_factors.map((factor, idx) => (
              <div key={idx} style={{ padding: '6px 8px', borderBottom: '1px solid var(--border-color)', fontSize: '12px', display: 'flex', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{factor.factor.replace(/_/g, ' ')}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{factor.description}</div>
                </div>
                <div style={{ textAlign: 'right', fontWeight: 600 }}>
                  {(factor.score * 100).toFixed(0)}%
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'block' }}>w: {factor.weight}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 4. Structured Evidence */}
        {evidence && (
          <div className="detail-section">
            <div className="detail-header">
              <span>Structured Evidence Engine ("WHY?")</span>
              <span className="badge badge-neutral">{evidence.verification_status}</span>
            </div>

            {evidence.evidence_items.map((evItem, idx) => (
              <div key={idx} style={{ padding: '8px 10px', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-color)', borderRadius: '6px', marginBottom: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 600, marginBottom: '2px' }}>
                  <span>{evItem.evidence_type.replace(/_/g, ' ')}</span>
                  <span className="badge badge-neutral" style={{ fontSize: '10px' }}>Source: {evItem.source}</span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-primary)', marginBottom: '4px' }}>
                  {evItem.interpretation}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Feature: <code>{evItem.feature_name}</code> = <strong>{evItem.value}</strong></span>
                  <span>Confidence: {(evItem.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 5. Historical Context */}
        {history && (
          <div className="detail-section">
            <div className="detail-header">
              <span>Historical Recurrence Telemetry</span>
            </div>

            <div className="info-grid" style={{ marginBottom: '12px' }}>
              <div className="info-item">
                <span className="info-item-label">30-Day Detections (1km)</span>
                <span className="info-item-value">{history.recurrence_count_30d}</span>
              </div>
              <div className="info-item">
                <span className="info-item-label">Historical Mean FRP</span>
                <span className="info-item-value">{history.historical_mean_frp ? `${history.historical_mean_frp.toFixed(1)} MW` : 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-item-label">FRP Anomaly Z-Score</span>
                <span className="info-item-value">{history.frp_anomaly_zscore ? history.frp_anomaly_zscore.toFixed(2) : 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-item-label">365-Day Recurrence</span>
                <span className="info-item-value">{history.recurrence_count_365d}</span>
              </div>
            </div>

            {history.nearby_historical_detections.length > 0 && (
              <div>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Recent Historical Detection Sequence
                </div>
                {history.nearby_historical_detections.slice(0, 5).map((det) => (
                  <div key={det.id} className="timeline-item">
                    <div className="timeline-dot" />
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                        <span style={{ fontWeight: 600 }}>{det.id}</span>
                        <span style={{ color: '#dc2626', fontWeight: 600 }}>{det.frp} MW</span>
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {new Date(det.acq_timestamp).toLocaleDateString()} | Dist: {det.distance_m.toFixed(0)}m
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 6. Human-in-the-Loop Analyst Review Form */}
        <div className="detail-section" style={{ backgroundColor: detail.review_required ? '#f5f3ff' : 'var(--bg-surface)' }}>
          <div className="detail-header">
            <span>Human-in-the-Loop Review</span>
            <span className="badge badge-neutral">Status: {detail.review_status || 'PENDING'}</span>
          </div>

          {detail.review_required && (
            <div style={{ padding: '10px 12px', backgroundColor: '#edd5ff', border: '1px solid #c084fc', borderRadius: '6px', marginBottom: '12px', color: '#581c87', fontSize: '12px' }}>
              <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '2px' }}>
                <ShieldAlert size={14} /> HUMAN INVESTIGATION RECOMMENDED
              </div>
              Model prediction confidence is below operational threshold or abstention rule was triggered. Analyst review required before action.
            </div>
          )}

          {reviewSuccessMsg && (
            <div style={{ padding: '8px 12px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534', borderRadius: '6px', fontSize: '12px', marginBottom: '12px' }}>
              <CheckCircle2 size={13} style={{ display: 'inline', marginRight: '4px' }} />
              {reviewSuccessMsg}
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Analyst ID</span>
              <input
                type="text"
                className="filter-input"
                value={reviewerId}
                onChange={(e) => setReviewerId(e.target.value)}
                placeholder="Enter Analyst ID (e.g. ANALYST-01)"
              />
            </div>

            <div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Investigation Notes</span>
              <textarea
                className="filter-input"
                style={{ height: '60px', resize: 'vertical' }}
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Record ground truth context, facility details, or escalation reasons..."
              />
            </div>

            {/* Optional Correction selector */}
            <div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                Select Corrected Label (Required if clicking Correct)
              </span>
              <select
                className="filter-select"
                value={selectedCorrectedClass}
                onChange={(e) => setSelectedCorrectedClass(e.target.value as ClassificationType)}
              >
                <option value="">-- Choose Correct Classification --</option>
                <option value="LIKELY_INDUSTRIAL_INCIDENT">Likely Industrial Incident</option>
                <option value="PERSISTENT_INDUSTRIAL_HEAT">Persistent Industrial Heat</option>
                <option value="NATURAL_WILDLAND_FIRE">Natural Wildland Fire</option>
              </select>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '4px' }}>
              <Button
                variant="success"
                size="sm"
                loading={submittingReview}
                icon={<CheckCircle2 size={12} />}
                onClick={() => handleSubmitReview('CONFIRMED')}
              >
                Confirm
              </Button>
              <Button
                variant="danger"
                size="sm"
                loading={submittingReview}
                icon={<XCircle size={12} />}
                onClick={() => handleSubmitReview('REJECTED')}
              >
                Reject
              </Button>
              <Button
                variant="secondary"
                size="sm"
                loading={submittingReview}
                icon={<ShieldAlert size={12} />}
                onClick={() => handleSubmitReview('ESCALATED')}
              >
                Escalate
              </Button>
              <Button
                variant="primary"
                size="sm"
                loading={submittingReview}
                disabled={!selectedCorrectedClass}
                icon={<Send size={12} />}
                onClick={() => handleSubmitReview('CORRECTED')}
              >
                Correct
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
