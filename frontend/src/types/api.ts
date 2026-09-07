/**
 * AstraFlare TypeScript API Interface Specifications.
 * Matches backend Pydantic schemas in backend/app/schemas/
 */

export type DataGovernanceSource = 'REAL' | 'SYNTHETIC_DEMO';

export type ClassificationType =
  | 'LIKELY_INDUSTRIAL_INCIDENT'
  | 'PERSISTENT_INDUSTRIAL_HEAT'
  | 'NATURAL_WILDLAND_FIRE'
  | 'UNLABELED';

export type RiskLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export type ReviewStatus = 'PENDING' | 'CONFIRMED' | 'REJECTED' | 'ESCALATED' | 'CORRECTED';

export type ReviewDecision = 'CONFIRMED' | 'REJECTED' | 'ESCALATED' | 'CORRECTED';

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  database: string;
  postgis: string;
  ml_model: string;
  version: string;
  environment: string;
}

export interface Hotspot {
  id: string;
  firms_id?: string | null;
  latitude: number;
  longitude: number;
  acq_timestamp: string;
  satellite: string;
  instrument?: string | null;
  brightness?: number | null;
  frp: number;
  confidence?: string | null;
  daynight?: string | null;
  data_source: DataGovernanceSource;
  physical_event_id?: string | null;
  classification?: ClassificationType | null;
  risk_level?: RiskLevel | null;
  review_required: boolean;
}

export type HotspotResponse = Hotspot;

export interface HotspotDetail extends Hotspot {
  nearest_industrial_name?: string | null;
  industrial_distance_m?: number | null;
  industrial_count_1km?: number;
  industrial_count_5km?: number;
  land_cover_code?: number | null;
  land_cover_name?: string | null;
  historical_count_30d?: number;
  historical_mean_frp?: number | null;
  frp_anomaly_zscore?: number | null;
  anomaly_status?: string;
  verification_status?: string;
  prediction_confidence?: number | null;
  review_status?: ReviewStatus;
}

export interface GeoJSONGeometry {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude] strictly RFC 7946
}

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: GeoJSONGeometry;
  properties: {
    id: string;
    latitude: number;
    longitude: number;
    acq_timestamp: string;
    satellite: string;
    frp: number;
    brightness?: number | null;
    classification?: ClassificationType | null;
    risk_level?: RiskLevel | null;
    review_required: boolean;
    data_source: DataGovernanceSource;
  };
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
}

export interface ClassProbabilities {
  LIKELY_INDUSTRIAL_INCIDENT: number;
  PERSISTENT_INDUSTRIAL_HEAT: number;
  NATURAL_WILDLAND_FIRE: number;
}

export interface PredictionResponse {
  hotspot_id: string;
  predicted_class: ClassificationType;
  confidence: number;
  probabilities: ClassProbabilities;
  review_required: boolean;
  human_review_threshold: number;
  model_version: string;
  model_status: string; // e.g. "RESEARCH BASELINE"
  limitations: string;
}

export interface EvidenceItem {
  evidence_type: string;
  feature_name: string;
  value: string;
  interpretation: string;
  source: string;
  confidence: number;
}

export interface EvidenceResponse {
  hotspot_id: string;
  physical_event_id?: string | null;
  verification_status: string;
  evidence_items: EvidenceItem[];
}

export interface RiskFactorItem {
  factor: string;
  weight: number;
  score: number;
  description: string;
}

export interface RiskResponse {
  hotspot_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  contributing_factors: RiskFactorItem[];
  explanation: string;
  limitations: string;
}

export interface HistoricalDetection {
  id: string;
  acq_timestamp: string;
  frp: number;
  satellite: string;
  distance_m: number;
}

export interface HistoryResponse {
  hotspot_id: string;
  physical_event_id?: string | null;
  recurrence_count_30d: number;
  recurrence_count_365d: number;
  historical_mean_frp?: number | null;
  frp_anomaly_zscore?: number | null;
  nearby_historical_detections: HistoricalDetection[];
}

export interface IndustrialSite {
  id: string;
  osm_id: string;
  name: string;
  facility_type: string;
  latitude: number;
  longitude: number;
  nearby_hotspots_3km_count: number;
}

export interface AnalyticsSummary {
  total_hotspots: number;
  total_events?: number;
  real_hotspots_count: number;
  synthetic_hotspots_count: number;
  total_reviews_submitted?: number;
  human_review_count?: number;
  events_near_industrial_facilities?: number;
  classification_breakdown?: Record<string, number>;
  hotspots_by_classification?: Record<string, number>;
  risk_breakdown?: Record<string, number>;
  events_by_risk_level?: Record<string, number>;
  sensor_breakdown?: Record<string, number>;
  sensor_distribution?: Record<string, number>;
  review_queue?: {
    pending_review_count: number;
    reviewed_count: number;
    decision_breakdown?: Record<string, number>;
  };
  land_cover_breakdown?: Record<string, number>;
  industrial_proximity_summary?: {
    within_1km_count: number;
    within_5km_count: number;
    mean_distance_m: number | null;
  };
}

export interface ReviewCreateRequest {
  decision: ReviewDecision;
  reviewer_id: string;
  notes?: string;
  corrected_classification?: ClassificationType;
}

export interface ReviewResponse {
  review_id: number;
  hotspot_id: string;
  original_prediction: string;
  final_classification: string;
  review_status: ReviewStatus;
  analyst_note?: string;
  reviewer_id?: string;
  created_at: string;
  updated_at: string;
}

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  meta: PaginationMeta;
}

export interface HotspotFilterParams {
  start_date?: string;
  end_date?: string;
  min_lat?: number;
  max_lat?: number;
  min_lon?: number;
  max_lon?: number;
  min_frp?: number;
  max_frp?: number;
  confidence?: string;
  classification?: ClassificationType;
  risk_level?: RiskLevel;
  review_required?: boolean;
  data_source?: DataGovernanceSource;
  page?: number;
  page_size?: number;
}
