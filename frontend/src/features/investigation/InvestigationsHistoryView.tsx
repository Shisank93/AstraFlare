import React, { useEffect, useState } from 'react';
import { ShieldCheck, RefreshCw, UserCheck } from 'lucide-react';
import { api } from '../../api/client';
import type { ReviewResponse } from '../../types/api';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ErrorState } from '../../components/common/ErrorState';

export const InvestigationsHistoryView: React.FC = () => {
  const [reviews, setReviews] = useState<ReviewResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInvestigations = () => {
    setLoading(true);
    setError(null);
    api
      .getInvestigations({ review_status: statusFilter || undefined, page_size: 100 })
      .then((data) => {
        setReviews(data.items);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load investigations history.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchInvestigations();
  }, [statusFilter]);

  return (
    <div style={{ padding: '24px', backgroundColor: 'var(--bg-app)', minHeight: 'calc(100vh - 54px)', overflowY: 'auto' }}>
      <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>Human-in-the-Loop Audit Log</h1>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            Complete audit trail of analyst review decisions, corrections, and escalations.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ width: '200px' }}
          >
            <option value="">All Review Decisions</option>
            <option value="CONFIRMED">CONFIRMED</option>
            <option value="REJECTED">REJECTED</option>
            <option value="ESCALATED">ESCALATED</option>
            <option value="CORRECTED">CORRECTED</option>
          </select>
          <Button variant="secondary" size="sm" icon={<RefreshCw size={12} />} onClick={fetchInvestigations}>
            Refresh
          </Button>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner message="Fetching analyst review history..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchInvestigations} />
      ) : reviews.length === 0 ? (
        <div style={{ backgroundColor: 'var(--bg-surface)', padding: '32px', textAlign: 'center', borderRadius: '8px', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
          <ShieldCheck size={32} style={{ marginBottom: '8px', opacity: 0.4 }} />
          <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>No Review Logs Recorded</div>
          <div style={{ fontSize: '12px', marginTop: '4px' }}>
            Analyst reviews submitted from the Operations map interface will appear in this audit log.
          </div>
        </div>
      ) : (
        <div style={{ backgroundColor: 'var(--bg-surface)', borderRadius: '8px', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-surface-subtle)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>
                <th style={{ padding: '12px 16px' }}>Review ID</th>
                <th style={{ padding: '12px 16px' }}>Hotspot ID</th>
                <th style={{ padding: '12px 16px' }}>Decision</th>
                <th style={{ padding: '12px 16px' }}>Original Prediction</th>
                <th style={{ padding: '12px 16px' }}>Final Classification</th>
                <th style={{ padding: '12px 16px' }}>Analyst</th>
                <th style={{ padding: '12px 16px' }}>Notes</th>
                <th style={{ padding: '12px 16px' }}>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {reviews.map((rev) => (
                <tr key={rev.review_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>#{rev.review_id}</td>
                  <td style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--accent-blue)' }}>{rev.hotspot_id}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <Badge
                      text={rev.review_status}
                      riskLevel={rev.review_status === 'CONFIRMED' ? 'LOW' : rev.review_status === 'REJECTED' ? 'HIGH' : 'MEDIUM'}
                    />
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>
                    {rev.original_prediction && rev.original_prediction !== 'UNKNOWN' && rev.original_prediction !== 'UNCLASSIFIED'
                      ? rev.original_prediction.replace(/_/g, ' ') 
                      : <span style={{ fontStyle: 'italic', opacity: 0.7 }}>Prediction unavailable</span>}
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>
                    {rev.final_classification && rev.final_classification !== 'UNKNOWN' && rev.final_classification !== 'UNCLASSIFIED'
                      ? rev.final_classification.replace(/_/g, ' ') 
                      : <span style={{ fontStyle: 'italic', opacity: 0.7 }}>Classification unavailable</span>}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
                      <UserCheck size={13} style={{ color: 'var(--accent-navy)' }} />
                      {rev.reviewer_id || 'ANALYST-01'}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', maxWidth: '240px' }}>
                    {rev.analyst_note || <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Notes unavailable</span>}
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: '12px' }}>
                    {new Date(rev.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
