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
  const [filterMode, setFilterMode] = React.useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');

  const highCount = hotspots.filter((h) => h.risk_level === 'HIGH').length;
  const mediumCount = hotspots.filter((h) => h.risk_level === 'MEDIUM').length;
  const lowCount = hotspots.filter((h) => h.risk_level === 'LOW').length;

  const displayHotspots = React.useMemo(() => {
    if (filterMode === 'HIGH') return hotspots.filter((h) => h.risk_level === 'HIGH');
    if (filterMode === 'MEDIUM') return hotspots.filter((h) => h.risk_level === 'MEDIUM');
    if (filterMode === 'LOW') return hotspots.filter((h) => h.risk_level === 'LOW');
    return hotspots;
  }, [hotspots, filterMode]);

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="panel-header" style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '10px 12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, fontSize: '13px', color: '#0f172a' }}>
            <AlertCircle size={14} style={{ color: '#ef4444' }} />
            Operational Queue ({displayHotspots.length})
          </div>
        </div>

        {/* Quick Filter Pills */}
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            onClick={() => setFilterMode('ALL')}
            style={{
              padding: '2px 8px',
              fontSize: '10px',
              fontWeight: 600,
              borderRadius: '4px',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: filterMode === 'ALL' ? '#0f172a' : '#f1f5f9',
              color: filterMode === 'ALL' ? '#ffffff' : '#64748b',
            }}
          >
            All ({hotspots.length})
          </button>
          <button
            onClick={() => setFilterMode('HIGH')}
            style={{
              padding: '2px 8px',
              fontSize: '10px',
              fontWeight: 600,
              borderRadius: '4px',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: filterMode === 'HIGH' ? '#ef4444' : '#fee2e2',
              color: filterMode === 'HIGH' ? '#ffffff' : '#b91c1c',
            }}
          >
            High ({highCount})
          </button>
          <button
            onClick={() => setFilterMode('MEDIUM')}
            style={{
              padding: '2px 8px',
              fontSize: '10px',
              fontWeight: 600,
              borderRadius: '4px',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: filterMode === 'MEDIUM' ? '#f59e0b' : '#fef3c7',
              color: filterMode === 'MEDIUM' ? '#ffffff' : '#b45309',
            }}
          >
            Med ({mediumCount})
          </button>
          <button
            onClick={() => setFilterMode('LOW')}
            style={{
              padding: '2px 8px',
              fontSize: '10px',
              fontWeight: 600,
              borderRadius: '4px',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: filterMode === 'LOW' ? '#10b981' : '#d1fae5',
              color: filterMode === 'LOW' ? '#ffffff' : '#047857',
            }}
          >
            Low ({lowCount})
          </button>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
        {displayHotspots.length === 0 ? (
          <div style={{ padding: '24px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
            No events match selected risk filter.
          </div>
        ) : (
          displayHotspots.map((h) => {
            const isSelected = h.id === selectedHotspotId;
            const isIncident = h.classification === 'LIKELY_INDUSTRIAL_INCIDENT';
            const isPersistent = h.classification === 'PERSISTENT_INDUSTRIAL_HEAT';
            const classColor = isIncident ? '#ef4444' : isPersistent ? '#f59e0b' : '#10b981';

            return (
              <div
                key={h.id}
                onClick={() => onSelectHotspot(h.id)}
                style={{
                  padding: '10px 12px',
                  borderRadius: '6px',
                  border: isSelected ? '2px solid #2563eb' : '1px solid var(--border-color)',
                  backgroundColor: isSelected ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-surface)',
                  marginBottom: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  boxShadow: isSelected ? '0 0 0 1px #2563eb' : 'none',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                  <div style={{ fontWeight: 600, fontSize: '12px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <MapPin size={12} style={{ color: classColor }} />
                    <span style={{ maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {h.id}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                    <Badge riskLevel={h.risk_level} />
                    {h.review_required && (
                      <span style={{ fontSize: '9px', fontWeight: 700, padding: '1px 5px', borderRadius: '3px', backgroundColor: '#f3e8ff', color: '#7c3aed', border: '1px solid #c084fc' }}>
                        REVIEW
                      </span>
                    )}
                  </div>
                </div>

                {/* Classification label */}
                {h.classification && (
                  <div style={{ fontSize: '10px', fontWeight: 700, color: classColor, marginBottom: '4px' }}>
                    {h.classification === 'LIKELY_INDUSTRIAL_INCIDENT' ? '🔥 LIKELY INDUSTRIAL INCIDENT' :
                     h.classification === 'PERSISTENT_INDUSTRIAL_HEAT' ? '🏭 PERSISTENT INDUSTRIAL HEAT' :
                     '🌲 NATURAL WILDLAND FIRE'}
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)' }}>
                  <span>
                    <Flame size={11} style={{ display: 'inline', marginRight: '3px', verticalAlign: '-1px' }} />
                    {h.frp} MW ({h.satellite})
                  </span>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                    {new Date(h.acq_timestamp).toLocaleDateString()}
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
