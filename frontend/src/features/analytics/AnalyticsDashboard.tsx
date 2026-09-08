import React, { useEffect, useState } from 'react';
import { Activity, AlertTriangle, Factory, PieChart, ShieldCheck, Layers } from 'lucide-react';
import { api } from '../../api/client';
import type { AnalyticsSummary } from '../../types/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ErrorState } from '../../components/common/ErrorState';

export const AnalyticsDashboard: React.FC = () => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = () => {
    setLoading(true);
    setError(null);
    api
      .getAnalyticsSummary()
      .then((data) => {
        setSummary(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch analytics summary from backend.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Calculating database-derived operational analytics..." />;
  }

  if (error || !summary) {
    return <ErrorState message={error || 'Analytics unavailable.'} onRetry={fetchAnalytics} />;
  }

  return (
    <div style={{ padding: '24px', backgroundColor: 'var(--bg-app)', minHeight: 'calc(100vh - 54px)', overflowY: 'auto' }}>
      <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>Operational Analytics Dashboard</h1>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            Real-time geospatial statistics derived directly from AstraFlare PostgreSQL telemetry database.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span className="badge badge-neutral" style={{ padding: '6px 12px', fontSize: '12px' }}>
            Dataset: NASA FIRMS (India)
          </span>
          <span className="badge badge-neutral" style={{ padding: '6px 12px', fontSize: '12px' }}>
            Data Governance: REAL ({summary.real_hotspots_count} loaded events)
          </span>
        </div>
      </div>

      {/* Top Metric Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <div style={{ backgroundColor: 'var(--bg-surface)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '12px', fontWeight: 600 }}>
            <span>TOTAL EVENTS</span>
            <Activity size={16} style={{ color: 'var(--accent-blue)' }} />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '8px' }}>
            {(summary.total_hotspots ?? summary.total_events ?? 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            {summary.real_hotspots_count ?? summary.total_events ?? 0} REAL | {summary.synthetic_hotspots_count ?? 0} DEMO
          </div>
        </div>

        <div style={{ backgroundColor: 'var(--bg-surface)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '12px', fontWeight: 600 }}>
            <span>HIGH RISK EVENTS</span>
            <AlertTriangle size={16} style={{ color: '#dc2626' }} />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#dc2626', marginTop: '8px' }}>
            {((summary.risk_breakdown && summary.risk_breakdown['HIGH']) || (summary.events_by_risk_level && summary.events_by_risk_level['HIGH']) || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Operational prioritization level: HIGH
          </div>
        </div>

        <div style={{ backgroundColor: 'var(--bg-surface)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '12px', fontWeight: 600 }}>
            <span>PENDING HUMAN ESCALATIONS</span>
            <ShieldCheck size={16} style={{ color: '#7c3aed' }} />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#7c3aed', marginTop: '8px' }}>
            {(summary.review_queue?.pending_review_count ?? summary.human_review_count ?? 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            {summary.review_queue?.reviewed_count ?? summary.total_reviews_submitted ?? 0} COMPLETED ANALYST REVIEWS
          </div>
        </div>

        <div style={{ backgroundColor: 'var(--bg-surface)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '12px', fontWeight: 600 }}>
            <span>INDUSTRIAL PROXIMITY EVENTS</span>
            <Factory size={16} style={{ color: 'var(--accent-navy)' }} />
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '8px' }}>
            {(summary.industrial_proximity_summary?.within_1km_count || summary.events_near_industrial_facilities || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            {summary.industrial_proximity_summary?.within_5km_count || summary.events_near_industrial_facilities || 0} near industrial facilities
          </div>
        </div>
      </div>

      {/* Main Breakdown Section Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>


        {/* Operational Risk Distribution */}
        <div style={{ backgroundColor: 'var(--bg-surface)', padding: '20px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <PieChart size={16} /> Operational Risk Distribution
          </div>
          {(Object.entries(summary.risk_breakdown || summary.events_by_risk_level || {}) as [string, number][]).map(([rk, count]) => {
            const pct = (summary.total_hotspots || summary.total_events || 0) > 0 ? (count / (summary.total_hotspots || summary.total_events || 1)) * 100 : 0;
            const barColor = rk === 'HIGH' ? '#dc2626' : rk === 'MEDIUM' ? '#d97706' : '#16a34a';
            return (
              <div key={rk} style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 600 }}>{rk} RISK</span>
                  <span>{count.toLocaleString()} ({pct.toFixed(1)}%)</span>
                </div>
                <div style={{ height: '8px', backgroundColor: 'var(--bg-surface-subtle)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${pct}%`, backgroundColor: barColor }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Satellite Sensor Distribution */}
        <div style={{ backgroundColor: 'var(--bg-surface)', padding: '20px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Layers size={16} /> SATELLITE SENSOR DISTRIBUTION
          </div>
          {(Object.entries(summary.sensor_breakdown || summary.sensor_distribution || {}) as [string, number][]).map(([sensor, count]) => {
            const pct = (summary.total_hotspots || summary.total_events || 0) > 0 ? (count / (summary.total_hotspots || summary.total_events || 1)) * 100 : 0;
            return (
              <div key={sensor} style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 600 }}>{sensor}</span>
                  <span>{count.toLocaleString()} ({pct.toFixed(1)}%)</span>
                </div>
                <div style={{ height: '8px', backgroundColor: 'var(--bg-surface-subtle)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${pct}%`, backgroundColor: 'var(--accent-navy)' }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Analyst Decision History */}
        <div style={{ backgroundColor: 'var(--bg-surface)', padding: '20px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ShieldCheck size={16} /> Analyst Review Decisions
          </div>
          {Object.keys(summary.review_queue?.decision_breakdown || {}).length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No completed analyst decisions yet.</div>
          ) : (
            Object.entries(summary.review_queue?.decision_breakdown || {}).map(([dec, count]) => (
              <div key={dec} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)', fontSize: '13px' }}>
                <span style={{ fontWeight: 600 }}>{dec}</span>
                <span className="badge badge-neutral">{count} Recorded</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
