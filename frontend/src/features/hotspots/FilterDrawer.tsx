import React from 'react';
import { Filter, RotateCcw } from 'lucide-react';
import type { HotspotFilterParams } from '../../types/api';

interface FilterDrawerProps {
  filters: HotspotFilterParams;
  onFilterChange: (updated: HotspotFilterParams) => void;
  onClearFilters: () => void;
  activeFilterCount: number;
}

export const FilterDrawer: React.FC<FilterDrawerProps> = ({
  filters,
  onFilterChange,
  onClearFilters,
  activeFilterCount,
}) => {
  const handleChange = (key: keyof HotspotFilterParams, value: any) => {
    onFilterChange({
      ...filters,
      [key]: value === '' ? undefined : value,
    });
  };

  return (
    <div>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Filter size={14} />
          Operational Filters
          {activeFilterCount > 0 && (
            <span className="badge badge-neutral" style={{ marginLeft: '4px' }}>
              {activeFilterCount} Active
            </span>
          )}
        </div>
        {activeFilterCount > 0 && (
          <button
            className="btn btn-sm"
            onClick={onClearFilters}
            style={{ fontSize: '11px', padding: '2px 6px' }}
          >
            <RotateCcw size={10} /> Reset
          </button>
        )}
      </div>

      {/* Date Range */}
      <div className="filter-group">
        <div className="filter-label">Acquisition Date Range</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Start Date</span>
            <input
              type="date"
              className="filter-input"
              value={filters.start_date || ''}
              onChange={(e) => handleChange('start_date', e.target.value)}
            />
          </div>
          <div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>End Date</span>
            <input
              type="date"
              className="filter-input"
              value={filters.end_date || ''}
              onChange={(e) => handleChange('end_date', e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Risk Level */}
      <div className="filter-group">
        <div className="filter-label">Prioritization Risk Level</div>
        <select
          className="filter-select"
          value={filters.risk_level || ''}
          onChange={(e) => handleChange('risk_level', e.target.value)}
        >
          <option value="">All Risk Levels</option>
          <option value="HIGH">HIGH Risk</option>
          <option value="MEDIUM">MEDIUM Risk</option>
          <option value="LOW">LOW Risk</option>
        </select>
      </div>

      {/* Classification */}
      <div className="filter-group">
        <div className="filter-label">Classification</div>
        <select
          className="filter-select"
          value={filters.classification || ''}
          onChange={(e) => handleChange('classification', e.target.value)}
        >
          <option value="">All Classifications</option>
          <option value="LIKELY_INDUSTRIAL_INCIDENT">Likely Industrial Incident</option>
          <option value="PERSISTENT_INDUSTRIAL_HEAT">Persistent Industrial Heat</option>
          <option value="NATURAL_WILDLAND_FIRE">Natural Wildland Fire</option>
        </select>
      </div>

      {/* FRP Range */}
      <div className="filter-group">
        <div className="filter-label">Fire Radiative Power (MW)</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <input
            type="number"
            className="filter-input"
            placeholder="Min FRP (MW)"
            min="0"
            value={filters.min_frp !== undefined ? filters.min_frp : ''}
            onChange={(e) => handleChange('min_frp', e.target.value ? Number(e.target.value) : '')}
          />
          <input
            type="number"
            className="filter-input"
            placeholder="Max FRP (MW)"
            min="0"
            value={filters.max_frp !== undefined ? filters.max_frp : ''}
            onChange={(e) => handleChange('max_frp', e.target.value ? Number(e.target.value) : '')}
          />
        </div>
      </div>

      {/* Review Required Checkbox */}
      <div className="filter-group">
        <label className="map-control-label" style={{ fontSize: '13px', fontWeight: 500 }}>
          <input
            type="checkbox"
            checked={!!filters.review_required}
            onChange={(e) => handleChange('review_required', e.target.checked ? true : undefined)}
          />
          Show Only Items Requiring Human Review
        </label>
      </div>
    </div>
  );
};
