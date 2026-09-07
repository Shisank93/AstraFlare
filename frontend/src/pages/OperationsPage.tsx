import React, { useEffect, useState, useMemo } from 'react';
import { api } from '../api/client';
import type {
  GeoJSONFeatureCollection,
  HotspotResponse,
  IndustrialSite,
  HotspotFilterParams,
  DataGovernanceSource,
} from '../types/api';
import { GISMap } from '../features/map/GISMap';
import { FilterDrawer } from '../features/hotspots/FilterDrawer';
import { AlertsList } from '../features/hotspots/AlertsList';
import { InvestigationPanel } from '../features/investigation/InvestigationPanel';
import { ErrorState } from '../components/common/ErrorState';
import { TestTube } from 'lucide-react';

interface OperationsPageProps {
  dataMode: DataGovernanceSource;
  setDataMode: (mode: DataGovernanceSource) => void;
}

export const OperationsPage: React.FC<OperationsPageProps> = ({ dataMode }) => {
  const [filters, setFilters] = useState<HotspotFilterParams>({
    data_source: dataMode,
  });
  const [geojson, setGeojson] = useState<GeoJSONFeatureCollection | null>(null);
  const [hotspotsList, setHotspotsList] = useState<HotspotResponse[]>([]);
  const [industrialSites, setIndustrialSites] = useState<IndustrialSite[]>([]);
  const [selectedHotspotId, setSelectedHotspotId] = useState<string | null>(null);

  const [loadingMap, setLoadingMap] = useState<boolean>(true);
  const [mapError, setMapError] = useState<string | null>(null);

  // Sync filters when top dataMode changes
  useEffect(() => {
    setFilters((prev) => ({
      ...prev,
      data_source: dataMode,
    }));
  }, [dataMode]);

  // Active filter count calculation
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.start_date) count++;
    if (filters.end_date) count++;
    if (filters.risk_level) count++;
    if (filters.classification) count++;
    if (filters.min_frp !== undefined) count++;
    if (filters.max_frp !== undefined) count++;
    if (filters.review_required) count++;
    return count;
  }, [filters]);

  // Load GeoJSON & Hotspots List when filters change
  const loadMapData = () => {
    setLoadingMap(true);
    setMapError(null);

    const targetSource = dataMode;

    Promise.all([
      api.getHotspotsGeoJSON({
        start_date: filters.start_date,
        end_date: filters.end_date,
        data_source: targetSource,
        limit: 1000,
      }),
      api.getHotspots({
        ...filters,
        data_source: targetSource,
        page_size: 200,
      }),
      api.getIndustrialSites({ page_size: 100 }),
    ])
      .then(([geoData, listData, indData]) => {
        setGeojson(geoData);
        setHotspotsList(listData.items);
        setIndustrialSites(indData.items);
        setLoadingMap(false);

        // Auto-select first hotspot if none selected
        if (!selectedHotspotId && listData.items.length > 0) {
          setSelectedHotspotId(listData.items[0].id);
        }
      })
      .catch((err) => {
        setMapError(err.message || 'Failed to load geospatial data from AstraFlare backend.');
        setLoadingMap(false);
      });
  };

  useEffect(() => {
    loadMapData();
  }, [filters, dataMode]);

  const handleClearFilters = () => {
    setFilters({ data_source: dataMode });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Controlled Demo Mode Header Banner */}
      {dataMode === 'SYNTHETIC_DEMO' && (
        <div style={{ backgroundColor: '#f5f3ff', borderBottom: '1px solid #ddd6fe', padding: '8px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontWeight: 600, color: '#5b21b6' }}>
            <TestTube size={15} />
            DEMO MODE · SYNTHETIC DATA FIXTURES (NOT LIVE NASA DATA)
          </div>

          {/* Scenario Selector */}
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', color: '#6d28d9', fontWeight: 600 }}>DEMO SCENARIOS:</span>
            <button
              className={`btn btn-sm ${selectedHotspotId === 'demo_hs_scenario_a' ? 'btn-primary' : ''}`}
              style={{ fontSize: '11px', padding: '3px 8px' }}
              onClick={() => setSelectedHotspotId('demo_hs_scenario_a')}
            >
              A: Industrial Incident
            </button>
            <button
              className={`btn btn-sm ${selectedHotspotId === 'demo_hs_scenario_b' ? 'btn-primary' : ''}`}
              style={{ fontSize: '11px', padding: '3px 8px' }}
              onClick={() => setSelectedHotspotId('demo_hs_scenario_b')}
            >
              B: Persistent Heat
            </button>
            <button
              className={`btn btn-sm ${selectedHotspotId === 'demo_hs_scenario_c' ? 'btn-primary' : ''}`}
              style={{ fontSize: '11px', padding: '3px 8px' }}
              onClick={() => setSelectedHotspotId('demo_hs_scenario_c')}
            >
              C: Natural Wildland Fire
            </button>
            <button
              className={`btn btn-sm ${selectedHotspotId === 'demo_hs_scenario_d' ? 'btn-primary' : ''}`}
              style={{ fontSize: '11px', padding: '3px 8px' }}
              onClick={() => setSelectedHotspotId('demo_hs_scenario_d')}
            >
              D: Human Review
            </button>
          </div>
        </div>
      )}

      {/* Main Operations Grid */}
      <div className="operations-layout" style={{ flex: 1 }}>
        {/* Left Sidebar: Filters & High Priority Alerts Queue */}
        <div className="sidebar-left">
          <FilterDrawer
            filters={filters}
            onFilterChange={(updated) => setFilters(updated)}
            onClearFilters={handleClearFilters}
            activeFilterCount={activeFilterCount}
          />

          <AlertsList
            hotspots={hotspotsList}
            selectedHotspotId={selectedHotspotId}
            onSelectHotspot={(id) => setSelectedHotspotId(id)}
          />
        </div>

        {/* Center: Full Interactive GIS Map */}
        <div style={{ position: 'relative', width: '100%', height: '100%' }}>
          {loadingMap && (
            <div style={{ position: 'absolute', top: 12, left: 60, zIndex: 1000, backgroundColor: 'var(--bg-surface)', padding: '4px 10px', borderRadius: '4px', fontSize: '11px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
              Loading telemetry...
            </div>
          )}
          {mapError ? (
            <ErrorState message={mapError} onRetry={loadMapData} />
          ) : (
            <GISMap
              geojson={geojson}
              industrialSites={industrialSites}
              selectedHotspotId={selectedHotspotId}
              onSelectHotspot={(id) => setSelectedHotspotId(id)}
            />
          )}
        </div>

        {/* Right Sidebar: Selected Hotspot Investigation Panel */}
        <div className="sidebar-right">
          <InvestigationPanel
            hotspotId={selectedHotspotId}
            onReviewSubmitted={loadMapData}
          />
        </div>
      </div>
    </div>
  );
};
