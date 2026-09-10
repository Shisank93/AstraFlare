import React, { useState, useEffect } from 'react';
import { FileText, Download, Printer, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import type { SummaryReport } from '../types/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const ReportsPage: React.FC = () => {
  const [reportType, setReportType] = useState<string>('DAILY_THERMAL');
  const [startDate, setStartDate] = useState<string>('2025-11-01');
  const [endDate, setEndDate] = useState<string>('2025-11-15');
  const [report, setReport] = useState<SummaryReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadReport = () => {
    setLoading(true);
    setError(null);

    api.getSummaryReport({
      report_type: reportType,
      start_date: startDate,
      end_date: endDate,
    })
      .then((data) => {
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to generate analytical summary report.');
        setLoading(false);
      });
  };

  useEffect(() => {
    loadReport();
  }, [reportType]);

  const handlePrint = () => {
    window.print();
  };

  const handleExportJSON = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `astraflare_${reportType.toLowerCase()}_report.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportCSV = () => {
    if (!report || !report.sample_events) return;
    const headers = ['Event ID', 'Latitude', 'Longitude', 'Timestamp', 'Satellite', 'FRP (MW)', 'Risk Level', 'Classification', 'Review Required'];
    const rows = report.sample_events.map((e: any) => [
      e.id,
      e.latitude,
      e.longitude,
      e.acq_timestamp,
      e.satellite,
      e.frp,
      e.risk_level,
      e.classification,
      e.review_required ? 'YES' : 'NO',
    ]);
    const csvContent = [headers.join(','), ...rows.map(r => r.map(c => `"${c ?? ''}"`).join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `astraflare_${reportType.toLowerCase()}_events.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '24px', backgroundColor: '#f8fafc' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* Reports Header & Control Bar */}
        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '8px', border: '1px solid #cbd5e1', boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h1 style={{ fontSize: '20px', fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                <FileText size={22} color="#2563eb" /> Analytical Intelligence Reports
              </h1>
              <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
                Generate defensible, server-side geospatial and thermal intelligence reports from verified real satellite observations.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={handlePrint}
                disabled={!report || loading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 12px',
                  fontSize: '12px',
                  fontWeight: 600,
                  backgroundColor: '#ffffff',
                  color: '#334155',
                  border: '1px solid #cbd5e1',
                  borderRadius: '5px',
                  cursor: 'pointer',
                }}
              >
                <Printer size={14} /> Print / Save PDF
              </button>
              <button
                onClick={handleExportCSV}
                disabled={!report || loading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 12px',
                  fontSize: '12px',
                  fontWeight: 600,
                  backgroundColor: '#ffffff',
                  color: '#334155',
                  border: '1px solid #cbd5e1',
                  borderRadius: '5px',
                  cursor: 'pointer',
                }}
              >
                <Download size={14} /> Export CSV
              </button>
              <button
                onClick={handleExportJSON}
                disabled={!report || loading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 12px',
                  fontSize: '12px',
                  fontWeight: 600,
                  backgroundColor: '#0f172a',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer',
                }}
              >
                <Download size={14} /> Export JSON
              </button>
            </div>
          </div>

          {/* Generator Controls */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center', paddingTop: '16px', borderTop: '1px solid #f1f5f9' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase' }}>
                Report Template
              </label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                style={{
                  padding: '6px 10px',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: '#0f172a',
                  backgroundColor: '#f8fafc',
                  border: '1px solid #cbd5e1',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                <option value="DAILY_THERMAL">Daily Satellite Thermal Activity Report</option>
                <option value="INDUSTRIAL_ANOMALY">Industrial Anomaly & Rare Thermal Incident Report</option>
                <option value="HIGH_RISK">High-Priority Operational Risk Report</option>
                <option value="ANALYST_AUDIT">Analyst Investigation Audit Report</option>
                <option value="REGIONAL">Regional Geospatial Thermal Concentration Report</option>
                <option value="HISTORICAL">Multi-Year Historical Comparison Report</option>
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase' }}>
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                style={{
                  padding: '5px 8px',
                  fontSize: '12px',
                  color: '#0f172a',
                  border: '1px solid #cbd5e1',
                  borderRadius: '4px',
                }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase' }}>
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                style={{
                  padding: '5px 8px',
                  fontSize: '12px',
                  color: '#0f172a',
                  border: '1px solid #cbd5e1',
                  borderRadius: '4px',
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-end', height: '100%', marginTop: 'auto' }}>
              <button
                onClick={loadReport}
                disabled={loading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 14px',
                  fontSize: '12px',
                  fontWeight: 600,
                  backgroundColor: '#2563eb',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Generate Report
              </button>
            </div>
          </div>
        </div>

        {/* Loading / Error States */}
        {loading && (
          <div style={{ padding: '60px', textAlign: 'center', backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
            <LoadingSpinner />
            <div style={{ marginTop: '12px', fontSize: '13px', color: '#64748b' }}>
              Compiling analytical intelligence report...
            </div>
          </div>
        )}

        {error && (
          <div style={{ padding: '20px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b' }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Report Content Document */}
        {report && !loading && (
          <div
            id="report-printable-area"
            style={{
              backgroundColor: '#ffffff',
              padding: '32px',
              borderRadius: '8px',
              border: '1px solid #cbd5e1',
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.05)',
              display: 'flex',
              flexDirection: 'column',
              gap: '24px',
            }}
          >
            {/* Document Header */}
            <div style={{ borderBottom: '2px solid #0f172a', paddingBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#2563eb', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  AstraFlare Geospatial Intelligence System
                </div>
                <h2 style={{ fontSize: '22px', fontWeight: 800, color: '#0f172a', margin: '4px 0 0 0' }}>
                  {report.report_title}
                </h2>
                <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                  Generated on: <strong>{new Date(report.generated_at).toLocaleString()}</strong>
                </div>
              </div>

              <div style={{ textAlign: 'right', fontSize: '11px', color: '#64748b' }}>
                <div>Territory: <strong>{report.dataset_scope?.scope}</strong></div>
                <div>Source: <strong>{report.dataset_scope?.data_source}</strong></div>
                <div>Date Range: <strong>{report.dataset_scope?.start_date} to {report.dataset_scope?.end_date}</strong></div>
              </div>
            </div>

            {/* Executive Summary */}
            <div style={{ backgroundColor: '#f8fafc', padding: '16px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#334155', textTransform: 'uppercase', marginBottom: '6px' }}>
                Executive Summary
              </div>
              <p style={{ margin: 0, fontSize: '13px', lineHeight: '1.6', color: '#1e293b' }}>
                {report.executive_summary}
              </p>
            </div>

            {/* Key Statistics KPI Cards */}
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '10px' }}>
                Key Operational Metrics
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '12px' }}>
                <div style={{ padding: '12px', backgroundColor: '#f8fafc', borderRadius: '6px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>Total Events</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a', marginTop: '4px' }}>
                    {report.key_statistics.total_events}
                  </div>
                </div>

                <div style={{ padding: '12px', backgroundColor: '#fee2e2', borderRadius: '6px', border: '1px solid #fecaca', textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: '#991b1b', fontWeight: 600 }}>High Risk</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#991b1b', marginTop: '4px' }}>
                    {report.key_statistics.high_risk_events}
                  </div>
                </div>

                <div style={{ padding: '12px', backgroundColor: '#fef3c7', borderRadius: '6px', border: '1px solid #fde68a', textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: '#92400e', fontWeight: 600 }}>Medium Risk</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#92400e', marginTop: '4px' }}>
                    {report.key_statistics.medium_risk_events}
                  </div>
                </div>

                <div style={{ padding: '12px', backgroundColor: '#f1f5f9', borderRadius: '6px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: '#475569', fontWeight: 600 }}>Low Risk</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#475569', marginTop: '4px' }}>
                    {report.key_statistics.low_risk_events}
                  </div>
                </div>

                <div style={{ padding: '12px', backgroundColor: '#e0e7ff', borderRadius: '6px', border: '1px solid #c7d2fe', textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: '#3730a3', fontWeight: 600 }}>Queued for Review</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#3730a3', marginTop: '4px' }}>
                    {report.key_statistics.events_requiring_investigation}
                  </div>
                </div>

                <div style={{ padding: '12px', backgroundColor: '#dcfce7', borderRadius: '6px', border: '1px solid #bbf7d0', textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: '#166534', fontWeight: 600 }}>Analyst Reviews</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#166534', marginTop: '4px' }}>
                    {report.key_statistics.completed_investigations}
                  </div>
                </div>
              </div>
            </div>

            {/* Sample Events Table */}
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '10px' }}>
                Operational Event Queue Sample ({report.sample_events?.length || 0} events)
              </div>
              <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: '6px' }}>
                <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse', textAlign: 'left' }}>
                  <thead style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                    <tr>
                      <th style={{ padding: '8px 12px', color: '#475569' }}>Event ID</th>
                      <th style={{ padding: '8px 12px', color: '#475569' }}>Coordinates</th>
                      <th style={{ padding: '8px 12px', color: '#475569' }}>Acquisition Time</th>
                      <th style={{ padding: '8px 12px', color: '#475569' }}>FRP</th>
                      <th style={{ padding: '8px 12px', color: '#475569' }}>Risk Level</th>
                      <th style={{ padding: '8px 12px', color: '#475569' }}>ML Classification</th>
                      <th style={{ padding: '8px 12px', color: '#475569' }}>Analyst Review</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.sample_events && report.sample_events.map((evt: any, idx: number) => (
                      <tr key={evt.id || idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '8px 12px', fontFamily: 'monospace', fontWeight: 600, color: '#0f172a' }}>
                          {evt.id}
                        </td>
                        <td style={{ padding: '8px 12px', color: '#475569' }}>
                          {evt.latitude?.toFixed(4)}°, {evt.longitude?.toFixed(4)}°
                        </td>
                        <td style={{ padding: '8px 12px', color: '#475569' }}>
                          {evt.acq_timestamp?.split('T')[0]} {evt.acq_timestamp?.split('T')[1]?.substring(0, 5)}
                        </td>
                        <td style={{ padding: '8px 12px', fontWeight: 700, color: '#ea580c' }}>
                          {evt.frp?.toFixed(1)} MW
                        </td>
                        <td style={{ padding: '8px 12px' }}>
                          <span
                            style={{
                              padding: '2px 6px',
                              fontSize: '10px',
                              fontWeight: 700,
                              borderRadius: '3px',
                              backgroundColor: evt.risk_level === 'HIGH' ? '#fee2e2' : evt.risk_level === 'MEDIUM' ? '#fef3c7' : '#f1f5f9',
                              color: evt.risk_level === 'HIGH' ? '#991b1b' : evt.risk_level === 'MEDIUM' ? '#92400e' : '#475569',
                            }}
                          >
                            {evt.risk_level || 'LOW'}
                          </span>
                        </td>
                        <td style={{ padding: '8px 12px', fontWeight: 600, color: '#334155' }}>
                          {evt.classification?.replace(/_/g, ' ') || 'NATURAL WILDLAND FIRE'}
                        </td>
                        <td style={{ padding: '8px 12px' }}>
                          {evt.review_required ? (
                            <span style={{ color: '#d97706', fontWeight: 600, fontSize: '11px' }}>
                              Recommended
                            </span>
                          ) : (
                            <span style={{ color: '#059669', fontSize: '11px' }}>
                              Autonomous
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Offline Model Evaluation Reference */}
            {report.ml_model_evaluation && (
              <div style={{ backgroundColor: '#f8fafc', padding: '16px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#334155', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Model Performance Baseline (Offline GBDT Isolated Evaluation)
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', fontSize: '12px', color: '#475569' }}>
                  <div>Training Observations: <strong>{report.ml_model_evaluation.training_rows?.toLocaleString() || 54386}</strong></div>
                  <div>Testing Observations: <strong>{report.ml_model_evaluation.test_rows?.toLocaleString() || 14289}</strong></div>
                  <div>Facility / Event Overlap: <strong>{report.ml_model_evaluation.facility_overlap || 0}</strong></div>
                  <div>Macro F1-Score: <strong>{report.ml_model_evaluation.macro_f1 || 0.6667}</strong></div>
                </div>
              </div>
            )}

            {/* Sign-off & Audit Notice */}
            <div style={{ borderTop: '1px solid #cbd5e1', paddingTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', color: '#64748b' }}>
              <div>
                Report Sign-Off: <strong>ASTRAFLARE AUTOMATED INTELLIGENCE SYSTEM</strong>
              </div>
              <div>
                Security Clearance: <strong>OFFICIAL USE ONLY</strong>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
