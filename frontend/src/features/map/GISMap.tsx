import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { Layers, Maximize2 } from 'lucide-react';
import type { GeoJSONFeatureCollection, IndustrialSite } from '../../types/api';

interface GISMapProps {
  geojson: GeoJSONFeatureCollection | null;
  industrialSites: IndustrialSite[];
  selectedHotspotId?: string | null;
  onSelectHotspot: (id: string) => void;
}

export const GISMap: React.FC<GISMapProps> = ({
  geojson,
  industrialSites,
  selectedHotspotId,
  onSelectHotspot,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const hotspotLayerRef = useRef<L.GeoJSON | null>(null);
  const industrialLayerRef = useRef<L.LayerGroup | null>(null);

  const [showHotspots, setShowHotspots] = useState(true);
  const [showIndustrial, setShowIndustrial] = useState(true);
  const [featureCount, setFeatureCount] = useState(0);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Default center over South Asia / India (20.5937, 78.9629)
    const map = L.map(mapContainerRef.current, {
      zoomControl: false,
      attributionControl: true,
    }).setView([20.5937, 78.9629], 5);

    // Zoom control at top left
    L.control.zoom({ position: 'topleft' }).addTo(map);

    // OpenStreetMap standard clean tile provider (no API key required)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    mapRef.current = map;

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Update Hotspot GeoJSON Layer
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Remove existing layer
    if (hotspotLayerRef.current) {
      map.removeLayer(hotspotLayerRef.current);
      hotspotLayerRef.current = null;
    }

    if (!geojson || !geojson.features || !showHotspots) {
      setFeatureCount(0);
      return;
    }

    setFeatureCount(geojson.features.length);

    const geojsonLayer = L.geoJSON(geojson as any, {
      pointToLayer: (feature, latlng) => {
        const props = feature.properties || {};
        const isSelected = props.id === selectedHotspotId;
        const riskLevel = (props.risk_level || 'LOW').toUpperCase();
        const isReviewRequired = props.review_required;

        let color = '#10b981'; // LOW: Emerald Green (Natural Wildland Fire)
        let fillColor = '#34d399';
        let classLabel = 'NATURAL WILDLAND FIRE';

        if (riskLevel === 'HIGH') {
          color = '#ef4444'; // HIGH: Vibrant Red (Industrial Incident)
          fillColor = '#f87171';
          classLabel = 'LIKELY INDUSTRIAL INCIDENT';
        } else if (riskLevel === 'MEDIUM') {
          color = '#f59e0b'; // MEDIUM: Amber Flame (Persistent Heat / High Recurrence)
          fillColor = '#fbbf24';
          classLabel = 'PERSISTENT INDUSTRIAL HEAT';
        }

        if (props.classification) {
          classLabel = props.classification.replace(/_/g, ' ');
        }

        const radius = isSelected ? 11 : isReviewRequired ? 8 : (riskLevel === 'HIGH' ? 8 : (riskLevel === 'MEDIUM' ? 7 : 6));
        const strokeWidth = isSelected ? 3.5 : (riskLevel === 'HIGH' ? 2.5 : 1.5);
        const strokeColor = isSelected ? '#ffffff' : (isReviewRequired ? '#8b5cf6' : color);

        const marker = L.circleMarker(latlng, {
          radius: radius,
          fillColor: fillColor,
          color: strokeColor,
          weight: strokeWidth,
          opacity: 1,
          fillOpacity: 0.9,
        });

        // Click handler
        marker.on('click', () => {
          if (props.id) {
            onSelectHotspot(props.id);
          }
        });

        // Rich tooltip
        const popupContent = `
          <div style="font-family: system-ui, -apple-system, sans-serif; padding: 4px 6px; min-width: 170px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
              <span style="font-weight: 700; font-size: 11px; color: #0f172a;">${props.id}</span>
              <span style="font-size: 9px; padding: 1px 5px; border-radius: 3px; font-weight: 700; background: ${color}20; color: ${color}; border: 1px solid ${color};">
                ${riskLevel} RISK
              </span>
            </div>
            <div style="font-size: 11px; font-weight: 700; color: ${color}; margin-bottom: 4px;">
              ${classLabel}
            </div>
            <div style="font-size: 11px; color: #475569; display: flex; justify-content: space-between; margin-bottom: 2px;">
              <span>Thermal FRP:</span>
              <strong style="color: #0f172a;">${props.frp} MW</strong>
            </div>
            <div style="font-size: 11px; color: #475569; display: flex; justify-content: space-between;">
              <span>Sensor:</span>
              <strong style="color: #0f172a;">${props.satellite || 'VIIRS'}</strong>
            </div>
            ${props.industrial_distance_m && props.industrial_distance_m <= 5000 ? `
            <div style="font-size: 10px; color: #b45309; margin-top: 4px; padding-top: 3px; border-top: 1px solid #e2e8f0; font-weight: 600;">
              🏭 ${Math.round(props.industrial_distance_m)}m to Industrial Facility
            </div>` : ''}
          </div>
        `;
        marker.bindTooltip(popupContent, { direction: 'top', offset: [0, -6] });

        return marker;
      },
    });

    geojsonLayer.addTo(map);
    hotspotLayerRef.current = geojsonLayer;

    // Auto-fit bounds if features exist and not manually moved
    if (geojson.features.length > 0) {
      try {
        const bounds = geojsonLayer.getBounds();
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
        }
      } catch (err) {
        // Bounds parsing fallback
      }
    }
  }, [geojson, showHotspots, selectedHotspotId, onSelectHotspot]);

  // Update Industrial Sites Layer
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (industrialLayerRef.current) {
      map.removeLayer(industrialLayerRef.current);
      industrialLayerRef.current = null;
    }

    if (!showIndustrial || !industrialSites || industrialSites.length === 0) {
      return;
    }

    const industrialMarkers: L.Marker[] = [];

    const factoryIcon = L.divIcon({
      className: 'custom-factory-icon',
      html: `
        <div style="
          background-color: #334155;
          color: white;
          width: 18px;
          height: 18px;
          border-radius: 3px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          font-weight: bold;
          border: 1px solid #ffffff;
          box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        ">🏭</div>
      `,
      iconSize: [18, 18],
      iconAnchor: [9, 9],
    });

    industrialSites.forEach((site) => {
      const marker = L.marker([site.latitude, site.longitude], { icon: factoryIcon });
      marker.bindTooltip(`
        <div>
          <strong>${site.name || 'Industrial Facility'}</strong><br/>
          Type: ${site.facility_type || 'Industrial Zone'}<br/>
          Nearby Hotspots (3km): ${site.nearby_hotspots_3km_count}
        </div>
      `, { direction: 'top' });
      industrialMarkers.push(marker);
    });

    const layerGroup = L.layerGroup(industrialMarkers);
    layerGroup.addTo(map);
    industrialLayerRef.current = layerGroup;
  }, [industrialSites, showIndustrial]);

  // Fit view to data
  const handleFitData = () => {
    if (mapRef.current && hotspotLayerRef.current) {
      try {
        const bounds = hotspotLayerRef.current.getBounds();
        if (bounds.isValid()) {
          mapRef.current.fitBounds(bounds, { padding: [40, 40] });
        }
      } catch (err) {
        // Fallback
      }
    }
  };

  return (
    <div className="map-container-area">
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

      {/* Floating Layer Controls & Categorized Legend */}
      <div className="map-controls-overlay" style={{ minWidth: '220px', padding: '10px 12px', fontSize: '11px', backgroundColor: 'rgba(255, 255, 255, 0.95)', backdropFilter: 'blur(6px)', border: '1px solid #cbd5e1', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
        <div style={{ fontWeight: 700, fontSize: '12px', color: '#0f172a', borderBottom: '1px solid #e2e8f0', paddingBottom: '6px', marginBottom: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Layers size={13} /> Geospatial Vectors
          </span>
          <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 600 }}>{featureCount} active</span>
        </div>

        {/* Legend categories */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', marginBottom: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '9px', height: '9px', borderRadius: '50%', backgroundColor: '#ef4444', border: '1.5px solid #b91c1c', display: 'inline-block' }} />
            <span style={{ fontWeight: 600, color: '#0f172a' }}>High Risk</span>
            <span style={{ color: '#64748b', fontSize: '10px' }}>· Industrial Incident</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '9px', height: '9px', borderRadius: '50%', backgroundColor: '#f59e0b', border: '1.5px solid #d97706', display: 'inline-block' }} />
            <span style={{ fontWeight: 600, color: '#0f172a' }}>Medium Risk</span>
            <span style={{ color: '#64748b', fontSize: '10px' }}>· Persistent Heat</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '9px', height: '9px', borderRadius: '50%', backgroundColor: '#10b981', border: '1.5px solid #047857', display: 'inline-block' }} />
            <span style={{ fontWeight: 600, color: '#0f172a' }}>Low Risk</span>
            <span style={{ color: '#64748b', fontSize: '10px' }}>· Natural Wildfire</span>
          </div>
        </div>

        {/* Layer Toggles */}
        <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label className="map-control-label" style={{ cursor: 'pointer', margin: 0, padding: '2px 0', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <input
              type="checkbox"
              checked={showHotspots}
              onChange={(e) => setShowHotspots(e.target.checked)}
            />
            <span>🔥 Thermal Anomalies</span>
          </label>
          <label className="map-control-label" style={{ cursor: 'pointer', margin: 0, padding: '2px 0', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <input
              type="checkbox"
              checked={showIndustrial}
              onChange={(e) => setShowIndustrial(e.target.checked)}
            />
            <span>🏭 Industrial Facilities ({industrialSites.length})</span>
          </label>
        </div>

        <div style={{ marginTop: '6px', paddingTop: '6px', borderTop: '1px solid #e2e8f0' }}>
          <button className="btn btn-sm" onClick={handleFitData} style={{ width: '100%', justifyContent: 'center' }} title="Fit to current dataset bounds">
            <Maximize2 size={12} /> Fit Active Bounds
          </button>
        </div>
      </div>
    </div>
  );
};
