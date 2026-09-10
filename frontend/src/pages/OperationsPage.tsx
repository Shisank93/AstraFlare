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
import { EventReportModal } from '../features/investigation/EventReportModal';
import { ErrorState } from '../components/common/ErrorState';
import { RefreshCw, Info } from 'lucide-react';

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
  const [reportModalEventId, setReportModalEventId] = useState<string | null>(null);

  const [loadingMap, setLoadingMap] = useState<boolean>(true);
  const [mapError, setMapError] = useState<string | null>(null);
  const [refreshingLive, setRefreshingLive] = useState<boolean>(false);
  const [liveStats, setLiveStats] = useState<{ last_updated?: string; new_observations?: number; new_events?: number } | null>(null);

  // Sync filters when top dataMode changes and fetch default dates
  useEffect(() => {
    let active = true;
    
    setFilters({ data_source: dataMode });
    
    // Fetch dataset metadata for proper default dates
    api.getMetadata(dataMode === 'REAL_LIVE' ? 'REAL' : dataMode)
      .then((meta) => {
        if (!active) return;
        if (meta.max_date) {
          const maxD = new Date(meta.max_date);
          const minD = new Date(maxD);
          minD.setDate(maxD.getDate() - 60);
          
          setFilters(prev => ({
            ...prev,
            start_date: minD.toISOString().split('T')[0],
            end_date: maxD.toISOString().split('T')[0]
          }));
        }
      })
      .catch((err) => {
        console.error("Failed to load metadata for default dates:", err);
      });
      
    return () => { active = false; };
  }, [dataMode]);

  // Active filter count calculation
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.start_date) count++;
    if (filters.end_date) count++;
    if (filters.risk_level) count++;
    if (filters.classification) count++;
    if (filters.min_frp) count++;
    if (filters.review_required !== undefined) count++;
    return count;
  }, [filters]);

  const loadMapData = () => {
    setLoadingMap(true);
    setMapError(null);

    const targetSource = dataMode;

    Promise.all([
      api.getHotspotsGeoJSON({
        start_date: filters.start_date,
        end_date: filters.end_date,
        data_source: targetSource,
        limit: 500,
      }),
      api.getHotspots({
        ...filters,
        data_source: targetSource,
        page_size: 100,
      }),
      api.getIndustrialSites({ page_size: 100 }),
    ])
      .then(([geo, list, ind]) => {
        setGeojson(geo);
        const items = list.items || [];
        setHotspotsList(items);
        setIndustrialSites(ind.items || []);
        
        // Auto-select first hotspot if none currently selected
        if (items.length > 0) {
          setSelectedHotspotId(prev => (prev && items.some(x => x.id === prev)) ? prev : items[0].id);
        } else {
          setSelectedHotspotId(null);
        }
        
        setLoadingMap(false);
      })
      .catch((err) => {
        setMapError(err.message || 'Unable to connect to AstraFlare backend service.');
        setLoadingMap(false);
      });
  };

  useEffect(() => {
    loadMapData();
  }, [filters, dataMode]);

  const handleClearFilters = () => {
    setFilters({ data_source: dataMode });
  };

  const handleLiveRefresh = async () => {
    setRefreshingLive(true);
    try {
      const res = await api.refreshLiveFirms('VIIRS_SNPP_NRT');
      setLiveStats({
        last_updated: res.last_updated || new Date().toLocaleTimeString(),
        new_observations: res.new_observations || res.inserted || 0,
        new_events: res.new_events || 0,
      });
      loadMapData();
    } catch (e: any) {
      alert(`NASA FIRMS Live Ingestion failed: ${e.message}`);
    } finally {
      setRefreshingLive(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* REAL LIVE Mode Header Banner */}
      {dataMode === 'REAL_LIVE' && (
        <div style={{ backgroundColor: '#fee2e2', borderBottom: '1px solid #fecaca', padding: '8px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 700, color: '#991b1b' }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#dc2626', animation: 'pulse 2s infinite' }} />
              LIVE NASA FIRMS FEED · INDIA
            </div>
            {liveStats && (
              <span style={{ fontSize: '11px', color: '#7f1d1d' }}>
                Last updated: <strong>{new Date(liveStats.last_updated!).toLocaleTimeString()}</strong> ({liveStats.new_observations} observations, {liveStats.new_events} events)
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '10px', color: '#991b1b', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Info size={11} /> Wide-area satellite intelligence complements on-site CCTV and sensors.
            </span>
            <button
              onClick={handleLiveRefresh}
              disabled={refreshingLive}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 700,
                backgroundColor: '#dc2626',
                color: '#ffffff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={12} className={refreshingLive ? 'animate-spin' : ''} />
              {refreshingLive ? 'Refreshing...' : 'Refresh Live NASA Data'}
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

        {/* Center: Leaflet GIS Visualizer */}
        <div className="map-container" style={{ position: 'relative' }}>
          {loadingMap && (
            <div
              style={{
                position: 'absolute',
                top: '12px',
                right: '12px',
                zIndex: 1000,
                backgroundColor: 'rgba(15, 23, 42, 0.85)',
                color: '#94a3b8',
                padding: '6px 12px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                border: '1px solid #334155',
                backdropFilter: 'blur(4px)',
              }}
            >
              <RefreshCw size={12} className="spin" />
              <span>SYNCING GEOSPATIAL VECTOR...</span>
            </div>
          )}
          {mapError ? (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ErrorState message={mapError} onRetry={loadMapData} />
            </div>
          ) : (
            <GISMap
              geojson={geojson}
              industrialSites={industrialSites}
              selectedHotspotId={selectedHotspotId}
              onSelectHotspot={(id) => setSelectedHotspotId(id)}
            />
          )}
        </div>

        {/* Right Sidebar: Selected Hotspot Deep Investigation */}
        <div className="sidebar-right">
          <InvestigationPanel
            hotspotId={selectedHotspotId}
            onReviewSubmitted={() => loadMapData()}
            onGenerateReport={(id) => setReportModalEventId(id)}
          />
        </div>
      </div>

      {/* Event Intelligence Dossier Modal */}
      {reportModalEventId && (
        <EventReportModal
          eventId={reportModalEventId}
          onClose={() => setReportModalEventId(null)}
        />
      )}
    </div>
  );
};
