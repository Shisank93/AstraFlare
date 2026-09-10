import React, { useEffect, useState } from 'react';
import { X, Printer, Download, ShieldCheck, Flame, MapPin, Brain, Activity, Clock, FileText } from 'lucide-react';
import { api } from '../../api/client';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

interface EventReportModalProps {
  eventId: string;
  onClose: () => void;
}

export const EventReportModal: React.FC<EventReportModalProps> = ({ eventId, onClose }) => {
  const [report, setReport] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getEventReport(eventId)
      .then((data) => {
        if (!isMounted) return;
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Failed to generate event intelligence dossier.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [eventId]);

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadJSON = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `astraflare_event_${eventId}_report.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.75)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
    >
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '8px',
          width: '100%',
          maxWidth: '900px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          overflow: 'hidden',
          border: '1px solid #cbd5e1',
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid #e2e8f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#0f172a',
            color: '#ffffff',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileText size={20} color="#38bdf8" />
            <div>
              <div style={{ fontSize: '15px', fontWeight: 700, letterSpacing: '0.02em' }}>
                EVENT INTELLIGENCE DOSSIER
              </div>
              <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                Identifier: <span style={{ fontFamily: 'monospace', color: '#f8fafc' }}>{eventId}</span>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={handlePrint}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '5px 10px',
                fontSize: '12px',
                fontWeight: 600,
                backgroundColor: '#1e293b',
                color: '#f8fafc',
                border: '1px solid #334155',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              <Printer size={13} /> Print / PDF
            </button>
            <button
              onClick={handleDownloadJSON}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '5px 10px',
                fontSize: '12px',
                fontWeight: 600,
                backgroundColor: '#1e293b',
                color: '#f8fafc',
                border: '1px solid #334155',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              <Download size={13} /> JSON
            </button>
            <button
              onClick={onClose}
              style={{
                padding: '5px',
                backgroundColor: 'transparent',
                border: 'none',
                color: '#94a3b8',
                cursor: 'pointer',
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', backgroundColor: '#f8fafc' }}>
          {loading && (
            <div style={{ padding: '60px', textAlign: 'center' }}>
              <LoadingSpinner />
              <div style={{ marginTop: '12px', fontSize: '13px', color: '#64748b' }}>
                Compiling multi-layer intelligence dossier...
              </div>
            </div>
          )}

          {error && (
            <div style={{ padding: '24px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', color: '#991b1b' }}>
              <strong>Failed to generate report:</strong> {error}
            </div>
          )}

          {report && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Header Status Bar */}
              <div
                style={{
                  backgroundColor: '#ffffff',
                  padding: '16px',
                  borderRadius: '6px',
                  border: '1px solid #e2e8f0',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: '16px',
                }}
              >
                <div>
                  <span style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
                    Report Generated
                  </span>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: '#0f172a', marginTop: '2px' }}>
                    {new Date(report.report_generated_at).toLocaleString()}
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
                    Operational Risk
                  </span>
                  <div style={{ marginTop: '2px' }}>
                    <span
                      style={{
                        padding: '3px 8px',
                        fontSize: '11px',
                        fontWeight: 700,
                        borderRadius: '4px',
                        backgroundColor:
                          report.operational_risk?.risk_level === 'HIGH'
                            ? '#fee2e2'
                            : report.operational_risk?.risk_level === 'MEDIUM'
                            ? '#fef3c7'
                            : '#f1f5f9',
                        color:
                          report.operational_risk?.risk_level === 'HIGH'
                            ? '#991b1b'
                            : report.operational_risk?.risk_level === 'MEDIUM'
                            ? '#92400e'
                            : '#475569',
                      }}
                    >
                      {report.operational_risk?.risk_level || 'LOW'} (Score: {report.operational_risk?.risk_score?.toFixed(3) || '0.000'})
                    </span>
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
                    ML Predicted Class
                  </span>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginTop: '2px' }}>
                    {report.ml_intelligence?.predicted_class?.replace(/_/g, ' ') || 'UNLABELED'}
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
                    Calibrated Confidence
                  </span>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#2563eb', marginTop: '2px' }}>
                    {report.ml_intelligence?.confidence != null ? `${(report.ml_intelligence.confidence * 100).toFixed(1)}%` : 'N/A'}
                  </div>
                </div>
              </div>

              {/* Telemetry & GIS Context Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                {/* Telemetry */}
                <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Flame size={15} color="#ea580c" /> Thermal Telemetry
                  </div>
                  <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                    <tbody>
                      <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '6px 0', color: '#64748b' }}>Centroid Coordinates</td>
                        <td style={{ padding: '6px 0', fontWeight: 600, textAlign: 'right' }}>
                          {report.telemetry.latitude?.toFixed(4)}°, {report.telemetry.longitude?.toFixed(4)}°
                        </td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '6px 0', color: '#64748b' }}>Acquisition Timestamp</td>
                        <td style={{ padding: '6px 0', fontWeight: 600, textAlign: 'right' }}>
                          {report.telemetry.acq_timestamp}
                        </td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '6px 0', color: '#64748b' }}>Fire Radiative Power (FRP)</td>
                        <td style={{ padding: '6px 0', fontWeight: 700, color: '#ea580c', textAlign: 'right' }}>
                          {report.telemetry.frp_mw?.toFixed(1)} MW
                        </td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '6px 0', color: '#64748b' }}>Brightness Temperature</td>
                        <td style={{ padding: '6px 0', fontWeight: 600, textAlign: 'right' }}>
                          {report.telemetry.brightness_k?.toFixed(1)} K
                        </td>
                      </tr>
                      <tr>
                        <td style={{ padding: '6px 0', color: '#64748b' }}>Satellite & Sensor</td>
                        <td style={{ padding: '6px 0', fontWeight: 600, textAlign: 'right' }}>
                          {report.telemetry.satellite}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* GIS Context */}
                <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <MapPin size={15} color="#2563eb" /> Geospatial & Infrastructure Context
                  </div>
                  <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                    <tbody>
                      <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '6px 0', color: '#64748b' }}>Industrial Distance</td>
                        <td style={{ padding: '6px 0', fontWeight: 700, color: '#0f172a', textAlign: 'right' }}>
                          {report.gis_context.industrial_distance}
                        </td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '6px 0', color: '#64748b' }}>Proximity Assessment</td>
                        <td style={{ padding: '6px 0', fontWeight: 600, textAlign: 'right' }}>
                          {report.gis_context.industrial_proximity_label}
                        </td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '6px 0', color: '#64748b' }}>Nearest Facility</td>
                        <td style={{ padding: '6px 0', fontWeight: 600, textAlign: 'right' }}>
                          {report.gis_context.nearest_facility}
                        </td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '6px 0', color: '#64748b' }}>ESA 10m WorldCover</td>
                        <td style={{ padding: '6px 0', fontWeight: 600, textAlign: 'right' }}>
                          {report.gis_context.land_cover}
                        </td>
                      </tr>
                      <tr>
                        <td style={{ padding: '6px 0', color: '#64748b' }}>Data Quality Status</td>
                        <td style={{ padding: '6px 0', fontWeight: 600, textAlign: 'right' }}>
                          {report.telemetry.data_quality_status}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Machine Learning Classification & Calibrated Probability */}
              <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Brain size={15} color="#7c3aed" /> Machine Learning Classification & Calibrated Distribution
                  </div>
                  <span
                    style={{
                      padding: '2px 8px',
                      fontSize: '10px',
                      fontWeight: 700,
                      backgroundColor: '#e0e7ff',
                      color: '#3730a3',
                      borderRadius: '4px',
                    }}
                  >
                    {report.ml_intelligence?.model_status || 'RESEARCH BASELINE'}
                  </span>
                </div>

                {report.ml_intelligence?.probabilities && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
                    {Object.entries(report.ml_intelligence.probabilities).map(([cls, p]: [string, any]) => (
                      <div key={cls}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '3px' }}>
                          <span style={{ fontWeight: 600, color: '#334155' }}>{cls.replace(/_/g, ' ')}</span>
                          <span style={{ fontWeight: 700, color: cls === report.ml_intelligence.predicted_class ? '#2563eb' : '#64748b' }}>
                            {(p * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div style={{ height: '8px', backgroundColor: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${p * 100}%`,
                              height: '100%',
                              backgroundColor: cls === report.ml_intelligence.predicted_class ? '#2563eb' : '#94a3b8',
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* TreeSHAP Explainability Factors */}
                {report.ml_intelligence?.top_contributing_features && report.ml_intelligence.top_contributing_features.length > 0 && (
                  <div style={{ marginTop: '12px', borderTop: '1px solid #f1f5f9', paddingTop: '12px' }}>
                    <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', marginBottom: '6px' }}>
                      Explainability Factors (TreeSHAP & Operational Weights)
                    </div>
                    <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px', color: '#334155', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {report.ml_intelligence.top_contributing_features.map((item: any, idx: number) => (
                        <li key={idx}>
                          <strong>{item.feature}:</strong> {item.statement || item.value}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Multi-Layer Evidence Dossier Table */}
              <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldCheck size={15} color="#059669" /> Multi-Layer Evidence Statements
                </div>
                <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                      <th style={{ padding: '8px 10px', color: '#475569' }}>Category</th>
                      <th style={{ padding: '8px 10px', color: '#475569' }}>Metric Value</th>
                      <th style={{ padding: '8px 10px', color: '#475569' }}>Analytical Interpretation</th>
                      <th style={{ padding: '8px 10px', color: '#475569' }}>Source Provenance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.evidence_dossier && report.evidence_dossier.map((ev: any, idx: number) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '8px 10px', fontWeight: 600, color: '#334155' }}>
                          {ev.category?.replace(/_/g, ' ') || ev.evidence_type?.replace(/_/g, ' ')}
                        </td>
                        <td style={{ padding: '8px 10px', fontWeight: 700, color: '#0f172a' }}>{ev.value}</td>
                        <td style={{ padding: '8px 10px', color: '#475569' }}>{ev.interpretation}</td>
                        <td style={{ padding: '8px 10px', fontSize: '11px', color: '#64748b' }}>{ev.source}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Historical 30-Day Recurrence & Analyst Audit */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                {/* Historical */}
                <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Clock size={15} color="#475569" /> Historical Recurrence Baseline
                  </div>
                  <div style={{ fontSize: '12px', color: '#475569', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      30-Day Detections (1km): <strong>{report.historical_baseline?.recurrence_count_30d || 0} detections</strong>
                    </div>
                    <div>
                      365-Day Detections (1km): <strong>{report.historical_baseline?.recurrence_count_365d || 0} detections</strong>
                    </div>
                    <div>
                      FRP Anomaly Z-Score: <strong>{report.historical_baseline?.frp_anomaly_zscore ? `+${report.historical_baseline.frp_anomaly_zscore.toFixed(2)} sigma` : 'Baseline (0.00 sigma)'}</strong>
                    </div>
                  </div>
                </div>

                {/* Analyst Audit Log */}
                <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Activity size={15} color="#059669" /> Human Analyst Review History
                  </div>
                  {report.analyst_audit_trail && report.analyst_audit_trail.length > 0 ? (
                    <div style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {report.analyst_audit_trail.map((rev: any, idx: number) => (
                        <div key={idx} style={{ padding: '6px', backgroundColor: '#f8fafc', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                          <div>
                            <strong>Decision:</strong> <span style={{ color: '#059669', fontWeight: 700 }}>{rev.decision}</span> | By: {rev.reviewer || 'ANALYST'}
                          </div>
                          {rev.analyst_note && <div style={{ color: '#64748b', marginTop: '2px' }}>"{rev.analyst_note}"</div>}
                          <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '2px' }}>{rev.created_at}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '12px', color: '#94a3b8', fontStyle: 'italic' }}>
                      No prior analyst reviews submitted for this event. Event currently queued for operational review.
                    </div>
                  )}
                </div>
              </div>

              {/* Scientific Limitations Footer */}
              <div style={{ padding: '12px', backgroundColor: '#f1f5f9', borderRadius: '4px', fontSize: '11px', color: '#64748b', fontStyle: 'italic' }}>
                Notice: AstraFlare operates in a verified Research Baseline capacity for wide-area thermal contextualization and operational queue prioritization. It complements on-site fire safety systems (CCTV, equipment sensors, physical response teams) and does not replace certified industrial alarm networks.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
