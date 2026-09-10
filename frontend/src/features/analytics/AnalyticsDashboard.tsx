import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ShieldCheck,
  Brain,
  Flame,
  Compass,
  CheckCircle,
  Layers
} from 'lucide-react';
import { api } from '../../api/client';
import type {
  AnalyticsSummary,
  AnalyticsThermal,
  AnalyticsML,
  AnalyticsGeospatial,
  AnalyticsRisk,
  AnalyticsInvestigations
} from '../../types/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ErrorState } from '../../components/common/ErrorState';

export const AnalyticsDashboard: React.FC = () => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [thermal, setThermal] = useState<AnalyticsThermal | null>(null);
  const [ml, setML] = useState<AnalyticsML | null>(null);
  const [geospatial, setGeospatial] = useState<AnalyticsGeospatial | null>(null);
  const [risk, setRisk] = useState<AnalyticsRisk | null>(null);
  const [investigations, setInvestigations] = useState<AnalyticsInvestigations | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAllAnalytics = () => {
    setLoading(true);
    setError(null);

    Promise.all([
      api.getAnalyticsSummary(),
      api.getAnalyticsThermal(),
      api.getAnalyticsML(),
      api.getAnalyticsGeospatial(),
      api.getAnalyticsRisk(),
      api.getAnalyticsInvestigations(),
    ])
      .then(([s, t, m, g, r, i]) => {
        setSummary(s);
        setThermal(t);
        setML(m);
        setGeospatial(g);
        setRisk(r);
        setInvestigations(i);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch analytical intelligence data.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchAllAnalytics();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Aggregating PostgreSQL telemetry & model metrics..." />;
  }

  if (error || !summary) {
    return <ErrorState message={error || 'Analytics data unavailable.'} onRetry={fetchAllAnalytics} />;
  }

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '24px', backgroundColor: '#f8fafc' }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* Dashboard Header */}
        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '8px', border: '1px solid #cbd5e1', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h1 style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={22} color="#2563eb" /> Geospatial & Thermal Analytical Intelligence Console
            </h1>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
              Defensible real-world telemetry aggregations across NASA FIRMS satellite observations, PostGIS spatial clusters, and GBDT model evaluations.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ padding: '4px 10px', backgroundColor: '#eff6ff', color: '#1d4ed8', borderRadius: '4px', fontSize: '11px', fontWeight: 700, border: '1px solid #bfdbfe' }}>
              4,993,080 NASA FIRMS OBSERVATIONS
            </span>
            <span style={{ padding: '4px 10px', backgroundColor: '#f1f5f9', color: '#334155', borderRadius: '4px', fontSize: '11px', fontWeight: 700, border: '1px solid #cbd5e1' }}>
              100 ACTIVE CLUSTERED EVENTS
            </span>
            <span style={{ padding: '4px 10px', backgroundColor: '#f0fdf4', color: '#15803d', borderRadius: '4px', fontSize: '11px', fontWeight: 700, border: '1px solid #bbf7d0' }}>
              96 INDUSTRIAL FACILITIES
            </span>
          </div>
        </div>

        {/* Section A: Executive Overview KPIs */}
        <div>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '10px' }}>
            A. Executive Operational Overview
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
            
            {/* Total Events */}
            <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, color: '#64748b' }}>
                <span>ACTIVE EVENTS</span>
                <Layers size={15} color="#2563eb" />
              </div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', marginTop: '6px' }}>
                {summary.total_events}
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                Clustered from ~4.99M observations
              </div>
            </div>

            {/* High Risk Events */}
            <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, color: '#dc2626' }}>
                <span>HIGH RISK QUEUE</span>
                <AlertTriangle size={15} color="#dc2626" />
              </div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#dc2626', marginTop: '6px' }}>
                {summary.risk_breakdown['HIGH'] || 0}
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                Operational prioritization level: HIGH
              </div>
            </div>

            {/* Medium Risk Events */}
            <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, color: '#d97706' }}>
                <span>MEDIUM RISK</span>
                <AlertTriangle size={15} color="#d97706" />
              </div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#d97706', marginTop: '6px' }}>
                {summary.risk_breakdown['MEDIUM'] || 0}
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                Operational prioritization level: MEDIUM
              </div>
            </div>

            {/* Low Risk Events */}
            <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, color: '#475569' }}>
                <span>LOW RISK</span>
                <ShieldCheck size={15} color="#475569" />
              </div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#475569', marginTop: '6px' }}>
                {summary.risk_breakdown['LOW'] || 0}
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                Remote / low severity baseline
              </div>
            </div>

            {/* Events Requiring Analyst Review */}
            <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, color: '#7c3aed' }}>
                <span>ANALYST QUEUE</span>
                <Brain size={15} color="#7c3aed" />
              </div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#7c3aed', marginTop: '6px' }}>
                {summary.human_review_queue?.pending_review_count || 0}
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                Low model confidence ($P &lt; 0.65$)
              </div>
            </div>

            {/* Completed Analyst Investigations */}
            <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, color: '#16a34a' }}>
                <span>COMPLETED AUDITS</span>
                <CheckCircle size={15} color="#16a34a" />
              </div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: '#16a34a', marginTop: '6px' }}>
                {summary.total_reviews_submitted || 0}
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                Verified human determinations
              </div>
            </div>
          </div>
        </div>

        {/* Section B: Thermal Activity Intelligence */}
        {thermal && (
          <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Flame size={16} color="#ea580c" /> B. Thermal Radiative Power & Sensor Intelligence
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
              
              {/* FRP Distribution Histogram */}
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '10px' }}>
                  FRP Intensity Distribution
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {Object.entries(thermal.frp_distribution).map(([bin, cnt]) => {
                    const total = summary.total_events || 1;
                    const pct = Math.round((Number(cnt) / total) * 100);
                    return (
                      <div key={bin}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '3px' }}>
                          <span style={{ color: '#334155', fontWeight: 600 }}>{bin}</span>
                          <span style={{ fontWeight: 700, color: '#ea580c' }}>{cnt} ({pct}%)</span>
                        </div>
                        <div style={{ height: '8px', backgroundColor: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{ width: `${Math.max(pct, cnt > 0 ? 5 : 0)}%`, height: '100%', backgroundColor: '#ea580c' }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Satellite Sensor Breakdown */}
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '10px' }}>
                  NASA FIRMS Sensor Telemetry Mix
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {Object.entries(thermal.satellite_distribution).map(([sat, cnt]) => (
                    <div key={sat}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '3px' }}>
                        <span style={{ color: '#334155', fontWeight: 600 }}>{sat}</span>
                        <span style={{ fontWeight: 700, color: '#2563eb' }}>{Number(cnt).toLocaleString()}</span>
                      </div>
                      <div style={{ height: '8px', backgroundColor: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${(Number(cnt) / 4993080) * 100}%`,
                            height: '100%',
                            backgroundColor: '#2563eb',
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Diurnal Solar/Infrared Ratio */}
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '10px' }}>
                  Diurnal Pass Distribution
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {Object.entries(thermal.diurnal_distribution).map(([mode, cnt]) => (
                    <div key={mode}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '3px' }}>
                        <span style={{ color: '#334155', fontWeight: 600 }}>{mode}</span>
                        <span style={{ fontWeight: 700, color: '#0f172a' }}>{Number(cnt).toLocaleString()}</span>
                      </div>
                      <div style={{ height: '8px', backgroundColor: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${(Number(cnt) / 4993080) * 100}%`,
                            height: '100%',
                            backgroundColor: mode.includes('Daytime') ? '#f59e0b' : '#334155',
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Section C: Machine Learning Intelligence & Offline Evaluation */}
        {ml && (
          <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Brain size={16} color="#7c3aed" /> C. Machine Learning Intelligence & Evaluation Audit
              </div>
              <span style={{ padding: '3px 8px', backgroundColor: '#e0e7ff', color: '#3730a3', borderRadius: '4px', fontSize: '10px', fontWeight: 700 }}>
                {ml.model_status}
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
              
              {/* Classification Breakdown */}
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '10px' }}>
                  Active Operational Classification Mix
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {Object.entries(ml.active_classification_distribution).map(([cls, cnt]) => (
                    <div key={cls}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '3px' }}>
                        <span style={{ color: '#334155', fontWeight: 600 }}>{cls.replace(/_/g, ' ')}</span>
                        <span style={{ fontWeight: 700, color: '#0f172a' }}>{cnt}</span>
                      </div>
                      <div style={{ height: '8px', backgroundColor: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${(Number(cnt) / 100) * 100}%`,
                            height: '100%',
                            backgroundColor: cls === 'NATURAL_WILDLAND_FIRE' ? '#16a34a' : cls === 'PERSISTENT_INDUSTRIAL_HEAT' ? '#2563eb' : '#dc2626',
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Abstention Rate Analytics */}
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '10px' }}>
                  Operational Abstention Policy ($P &lt; 0.65$)
                </div>
                <div style={{ padding: '12px', backgroundColor: '#f8fafc', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#64748b' }}>Autonomous Classifications:</span>
                    <strong style={{ color: '#16a34a' }}>{ml.abstention_summary.autonomous_classification} events</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#64748b' }}>Abstained for Human Review:</span>
                    <strong style={{ color: '#d97706' }}>{ml.abstention_summary.abstained_for_analyst_review} events</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#64748b' }}>Operational Abstention Rate:</span>
                    <strong style={{ color: '#2563eb' }}>{ml.abstention_summary.abstention_rate}%</strong>
                  </div>
                  <p style={{ margin: '6px 0 0 0', fontSize: '10px', color: '#64748b', fontStyle: 'italic' }}>
                    Abstention is an active safety policy indicating lack of autonomous statistical confidence; it is not a system failure.
                  </p>
                </div>
              </div>

              {/* Confusion Matrix & Offline Evaluation */}
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '10px' }}>
                  Facility-Isolated Test Partition Evaluation
                </div>
                <div style={{ padding: '12px', backgroundColor: '#f8fafc', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '11px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '8px' }}>
                    <div>Training Set: <strong>{ml.offline_evaluation.training_rows.toLocaleString()}</strong></div>
                    <div>Test Set: <strong>{ml.offline_evaluation.test_rows.toLocaleString()}</strong></div>
                    <div>Macro F1: <strong>{ml.offline_evaluation.macro_f1}</strong></div>
                    <div>Weighted F1: <strong>{ml.offline_evaluation.weighted_f1}</strong></div>
                  </div>
                  <div style={{ fontSize: '10px', color: '#64748b', borderTop: '1px solid #e2e8f0', paddingTop: '6px' }}>
                    Wildland F1: <strong>1.0</strong> | Persistent Heat F1: <strong>1.0</strong> | Industrial Incident: <strong>0.0 (Data-Limited)</strong>
                  </div>
                </div>
              </div>
            </div>

            {/* Model Validation Targets Roadmap */}
            <div style={{ marginTop: '16px', borderTop: '1px solid #f1f5f9', paddingTop: '12px' }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '6px' }}>
                Next Validation Targets & Research Roadmap
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '8px' }}>
                {ml.validation_roadmap.map((item, idx) => (
                  <div key={idx} style={{ fontSize: '11px', color: '#334155', padding: '6px 10px', backgroundColor: '#f8fafc', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Section D: Geospatial & Risk Intelligence */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
          
          {/* Geospatial Proximity & Land Cover */}
          {geospatial && (
            <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Compass size={16} color="#059669" /> D. Geospatial Infrastructure & Biome Context
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Industrial Facility Proximity Bins
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {Object.entries(geospatial.industrial_proximity_distribution).map(([bin, cnt]) => (
                    <div key={bin} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                      <span style={{ color: '#334155' }}>{bin}:</span>
                      <strong style={{ color: '#0f172a' }}>{cnt} events</strong>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '12px' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '8px' }}>
                  ESA 10m WorldCover Surface Land Class
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {Object.entries(geospatial.land_cover_distribution).map(([lc, cnt]) => (
                    <div key={lc} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                      <span style={{ color: '#334155' }}>{lc}:</span>
                      <strong style={{ color: '#0f172a' }}>{cnt} events</strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Operational Prioritization Risk Analysis */}
          {risk && (
            <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AlertTriangle size={16} color="#ea580c" /> E. Operational Prioritization Risk Engine
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Operational Risk Tier Breakdown
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {Object.entries(risk.risk_level_breakdown).map(([lvl, data]: [string, any]) => (
                    <div key={lvl} style={{ padding: '8px', backgroundColor: '#f8fafc', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700 }}>
                        <span style={{ color: lvl === 'HIGH' ? '#dc2626' : lvl === 'MEDIUM' ? '#d97706' : '#475569' }}>
                          {lvl} RISK
                        </span>
                        <span>{data.count} events</span>
                      </div>
                      <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
                        Avg Score: {data.avg_risk_score} | Mean FRP: {data.avg_frp} MW
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '10px', fontSize: '11px', color: '#64748b', fontStyle: 'italic' }}>
                {risk.operational_note}
              </div>
            </div>
          )}

          {/* Investigation Queue Status */}
          {investigations && (
            <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldCheck size={16} color="#2563eb" /> F. Human Analyst Audit & Verification Status
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '12px', color: '#64748b' }}>Queue Completion:</span>
                <span style={{ fontSize: '15px', fontWeight: 800, color: '#16a34a' }}>
                  {investigations.queue_completion_rate}%
                </span>
              </div>

              <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '8px' }}>
                Recorded Determinations ({investigations.total_analyst_decisions} reviews)
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {Object.entries(investigations.decision_distribution).map(([dec, cnt]) => (
                  <div key={dec} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                    <span style={{ color: '#334155' }}>{dec}:</span>
                    <strong style={{ color: '#0f172a' }}>{cnt}</strong>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* System Architecture Positioning Note */}
        <div style={{ padding: '16px', backgroundColor: '#f1f5f9', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '11px', color: '#475569', lineHeight: '1.5' }}>
          <strong>AstraFlare System Context:</strong> AstraFlare delivers wide-area satellite thermal anomaly contextualization, calibrated multi-class machine learning classification, and operational prioritization risk scores. It is engineered to complement on-premises safety infrastructure (such as closed-circuit visual monitoring, equipment-level thermal sensors, and dedicated emergency response units) rather than replace certified on-site industrial safety systems.
        </div>
      </div>
    </div>
  );
};
