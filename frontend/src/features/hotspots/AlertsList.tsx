import React from 'react';
import { AlertCircle, Flame, MapPin } from 'lucide-react';
import type { HotspotResponse } from '../../types/api';
import { Badge } from '../../components/common/Badge';

interface AlertsListProps {
  hotspots: HotspotResponse[];
  selectedHotspotId?: string | null;
  onSelectHotspot: (id: string) => void;
}

export const AlertsList: React.FC<AlertsListProps> = ({
  hotspots,
  selectedHotspotId,
  onSelectHotspot,
}) => {
  // Priority filter: HIGH risk OR review_required
  const priorityHotspots = hotspots.filter(
    (h) => h.risk_level === 'HIGH' || h.review_required
  );

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <AlertCircle size={14} style={{ color: '#dc2626' }} />
          High Priority Operational Queue ({priorityHotspots.length})
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
        {priorityHotspots.length === 0 ? (
          <div style={{ padding: '24px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
            No high-priority alerts in current viewport filter.
          </div>
        ) : (
          priorityHotspots.map((h) => {
            const isSelected = h.id === selectedHotspotId;
            return (
              <div
                key={h.id}
                onClick={() => onSelectHotspot(h.id)}
                style={{
                  padding: '10px 12px',
                  borderRadius: '6px',
                  border: isSelected ? '2px solid var(--accent-blue)' : '1px solid var(--border-color)',
                  backgroundColor: isSelected ? 'var(--accent-blue-light)' : 'var(--bg-surface)',
                  marginBottom: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                  <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <MapPin size={12} style={{ color: 'var(--accent-navy)' }} />
                    {h.id}
                  </div>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <Badge riskLevel={h.risk_level} />
                    {h.review_required && <Badge reviewRequired={true} text="REVIEW" />}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  <span>
                    <Flame size={11} style={{ display: 'inline', marginRight: '3px', verticalAlign: '-1px' }} />
                    {h.frp} MW ({h.satellite})
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {new Date(h.acq_timestamp).toLocaleDateString()} {new Date(h.acq_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
