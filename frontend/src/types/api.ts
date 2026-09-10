/**
 * AstraFlare TypeScript API Interface Specifications.
 * Matches backend Pydantic schemas in backend/app/schemas/
 */

export type DataGovernanceSource = 'REAL' | 'REAL_LIVE';

export type ClassificationType =
  | 'LIKELY_INDUSTRIAL_INCIDENT'
  | 'PERSISTENT_INDUSTRIAL_HEAT'
  | 'NATURAL_WILDLAND_FIRE'
  | 'UNLABELED';

export type RiskLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export type PriorityLevel = 'URGENT' | 'HIGH' | 'MEDIUM' | 'LOW';

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
  priority?: PriorityLevel | null;
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
  duration_hours?: number | null;
  observation_count?: number | null;
  data_quality_status?: string;
  evidence_status?: string;
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
    priority?: PriorityLevel | null;
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

export interface ContributingFeature {
  feature: string;
  value: string;
  statement: string;
  contribution: number;
}

export interface PredictionResponse {
  hotspot_id: string;
  predicted_class?: ClassificationType | null;
  confidence?: number | null;
  probabilities?: ClassProbabilities | null;
  review_required: boolean;
  human_review_threshold: number;
  confidence_status?: string | null;
  abstention_reason?: string | null;
  industrial_anomaly_score?: number | null;
  industrial_anomaly_level?: 'HIGH' | 'MODERATE' | 'LOW' | null;
  top_contributing_features?: ContributingFeature[];
  model_version: string;
  model_status: string; // e.g. "RESEARCH BASELINE"
  limitations: string;
  is_ml_prediction: boolean;
  reference_label?: string | null;
  reference_provenance?: string | null;
  model_metadata?: any;
}

export interface EvidenceItem {
  category?: string;
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
  total_events: number;
  total_observations_ingested: number;
  total_industrial_sites_mapped: number;
  total_reviews_submitted: number;
  risk_breakdown: Record<string, number>;
  priority_breakdown: Record<string, number>;
  human_review_queue: {
    pending_review_count: number;
    reviewed_count: number;
    percentage_requiring_review: number;
  };
  events_near_industrial_facilities: number;
  model_governance: {
    status: string;
    macro_f1: number;
    abstention_threshold: number;
  };
}

export interface AnalyticsThermal {
  frp_distribution: Record<string, number>;
  daily_timeline: Array<{ date: string; events: number; mean_frp: number; peak_frp: number }>;
  satellite_distribution: Record<string, number>;
  diurnal_distribution: Record<string, number>;
}

export interface AnalyticsML {
  model_version: string;
  model_name: string;
  model_status: string;
  training_date: string;
  active_classification_distribution: Record<string, number>;
  abstention_summary: {
    total_scored: number;
    abstained_for_analyst_review: number;
    autonomous_classification: number;
    abstention_rate: number;
    threshold: number;
  };
  offline_evaluation: {
    training_rows: number;
    test_rows: number;
    facility_overlap: number;
    event_overlap: number;
    macro_f1: number;
    weighted_f1: number;
    accuracy: number;
    per_class_f1: Record<string, number>;
    confusion_matrix: number[][];
  };
  validation_roadmap: string[];
}

export interface AnalyticsGeospatial {
  industrial_proximity_distribution: Record<string, number>;
  land_cover_distribution: Record<string, number>;
}

export interface AnalyticsRisk {
  risk_level_breakdown: Record<string, { count: number; avg_risk_score: number; avg_frp: number }>;
  investigation_priorities: Record<string, number>;
  operational_note: string;
}

export interface AnalyticsInvestigations {
  total_analyst_decisions: number;
  pending_in_queue: number;
  decision_distribution: Record<string, number>;
  queue_completion_rate: number;
}

export interface EventReport {
  event_id: string;
  report_generated_at: string;
  telemetry: {
    latitude: number;
    longitude: number;
    acq_timestamp: string;
    satellite: string;
    frp_mw: number;
    brightness_k: number;
    duration_hours: number;
    observation_count: number;
    data_source: string;
    data_quality_status: string;
  };
  gis_context: {
    industrial_distance: string;
    industrial_distance_meters: number;
    industrial_proximity_label: string;
    nearest_facility: string;
    land_cover: string;
  };
  ml_intelligence: PredictionResponse;
  operational_risk: RiskResponse;
  evidence_dossier: EvidenceItem[];
  historical_baseline: HistoryResponse;
  analyst_audit_trail: any[];
}

export interface SummaryReport {
  report_title: string;
  report_type: string;
  generated_at: string;
  dataset_scope: {
    scope: string;
    data_source: string;
    start_date: string;
    end_date: string;
    total_satellite_observations: number;
    active_physical_events: number;
  };
  executive_summary: string;
  key_statistics: {
    total_events: number;
    high_risk_events: number;
    medium_risk_events: number;
    low_risk_events: number;
    events_requiring_investigation: number;
    completed_investigations: number;
  };
  sample_events: Hotspot[];
  ml_model_evaluation: any;
  operational_risk_summary: any;
}

export interface LiveRefreshResponse {
  status: string;
  country: string;
  source: string;
  last_updated: string;
  new_observations: number;
  new_events: number;
  inserted: number;
  duplicates: number;
  rejected: number;
  data_source: string;
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
  priority?: PriorityLevel;
  review_required?: boolean;
  satellite?: string;
  near_industry?: boolean;
  data_source?: DataGovernanceSource;
  page?: number;
  page_size?: number;
}
