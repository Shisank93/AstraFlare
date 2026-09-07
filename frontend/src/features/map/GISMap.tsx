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

        let color = '#16a34a'; // LOW: Green
        let fillColor = '#dcfce7';

        if (riskLevel === 'HIGH') {
          color = '#dc2626'; // HIGH: Red
          fillColor = '#fee2e2';
        } else if (riskLevel === 'MEDIUM') {
          color = '#d97706'; // MEDIUM: Amber
          fillColor = '#fef3c7';
        }

        if (isReviewRequired) {
          color = '#7c3aed'; // REVIEW REQUIRED: Purple accent
        }

        const radius = isSelected ? 10 : isReviewRequired ? 8 : 6;
        const strokeWidth = isSelected ? 3 : 1.5;

        const marker = L.circleMarker(latlng, {
          radius: radius,
          fillColor: fillColor,
          color: color,
          weight: strokeWidth,
          opacity: 1,
          fillOpacity: 0.85,
        });

        // Click handler
        marker.on('click', () => {
          if (props.id) {
            onSelectHotspot(props.id);
          }
        });

        // Popup hover/click info
        const popupContent = `
          <div style="font-family: sans-serif; padding: 4px;">
            <div class="popup-title">Hotspot: ${props.id}</div>
            <div class="popup-row">
              <span class="popup-label">FRP:</span>
              <span class="popup-val">${props.frp} MW</span>
            </div>
            <div class="popup-row">
              <span class="popup-label">Satellite:</span>
              <span class="popup-val">${props.satellite}</span>
            </div>
            <div class="popup-row">
              <span class="popup-label">Risk:</span>
              <span class="popup-val" style="font-weight: 700; color: ${color}">${riskLevel}</span>
            </div>
            ${props.classification ? `
            <div class="popup-row">
              <span class="popup-label">Class:</span>
              <span class="popup-val">${props.classification.replace(/_/g, ' ')}</span>
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

      {/* Floating Layer Controls & Legend */}
      <div className="map-controls-overlay">
        <div style={{ fontWeight: 600, borderBottom: '1px solid var(--border-color)', paddingBottom: '4px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Layers size={14} /> Map Layers ({featureCount} Observations)
        </div>
        <label className="map-control-label">
          <input
            type="checkbox"
            checked={showHotspots}
            onChange={(e) => setShowHotspots(e.target.checked)}
          />
          <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#dc2626' }}></span>
          Thermal Anomalies
        </label>
        <label className="map-control-label">
          <input
            type="checkbox"
            checked={showIndustrial}
            onChange={(e) => setShowIndustrial(e.target.checked)}
          />
          <span>🏭</span> Industrial Facilities ({industrialSites.length})
        </label>

        <div style={{ marginTop: '6px', paddingTop: '6px', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '6px' }}>
          <button className="btn btn-sm" onClick={handleFitData} title="Fit to current dataset bounds">
            <Maximize2 size={12} /> Fit Bounds
          </button>
        </div>
      </div>
    </div>
  );
};
