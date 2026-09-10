import type {
  HealthResponse,
  HotspotResponse,
  HotspotDetail,
  GeoJSONFeatureCollection,
  PredictionResponse,
  EvidenceResponse,
  RiskResponse,
  HistoryResponse,
  IndustrialSite,
  AnalyticsSummary,
  ReviewCreateRequest,
  ReviewResponse,
  PaginatedResponse,
  HotspotFilterParams,
} from '../types/api';

const getApiBaseUrl = () => {
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (typeof window !== 'undefined' && window.location && window.location.hostname) {
    return `http://${window.location.hostname}:8000`;
  }
  return 'http://127.0.0.1:8000';
};

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });
  } catch (error: any) {
    throw new NetworkError(`Unable to reach AstraFlare backend: ${error.message || 'Connection failed'}`);
  }

  if (!response.ok) {
    let errorDetail = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // Failed to parse JSON error, keep default
    }
    throw new ApiError(errorDetail, response.status);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // System Health
  async getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/health');
  },

  // Hotspots
  async getHotspots(params: HotspotFilterParams = {}): Promise<PaginatedResponse<HotspotResponse>> {
    const query = new URLSearchParams();
    if (params.start_date) query.set('start_date', params.start_date);
    if (params.end_date) query.set('end_date', params.end_date);
    if (params.min_lat !== undefined) query.set('min_lat', String(params.min_lat));
    if (params.max_lat !== undefined) query.set('max_lat', String(params.max_lat));
    if (params.min_lon !== undefined) query.set('min_lon', String(params.min_lon));
    if (params.max_lon !== undefined) query.set('max_lon', String(params.max_lon));
    if (params.min_frp !== undefined) query.set('min_frp', String(params.min_frp));
    if (params.max_frp !== undefined) query.set('max_frp', String(params.max_frp));
    if (params.confidence) query.set('confidence', params.confidence);
    if (params.classification) query.set('classification', params.classification);
    if (params.risk_level) query.set('risk_level', params.risk_level);
    if (params.review_required !== undefined) query.set('review_required', String(params.review_required));
    if (params.data_source) query.set('data_source', params.data_source);
    if (params.page) query.set('page', String(params.page));
    if (params.page_size) query.set('page_size', String(params.page_size));

    const queryString = query.toString();
    return request<PaginatedResponse<HotspotResponse>>(`/api/hotspots${queryString ? `?${queryString}` : ''}`);
  },

  async getHotspotsGeoJSON(params: {
    start_date?: string;
    end_date?: string;
    data_source?: string;
    limit?: number;
  } = {}): Promise<GeoJSONFeatureCollection> {
    const query = new URLSearchParams();
    if (params.start_date) query.set('start_date', params.start_date);
    if (params.end_date) query.set('end_date', params.end_date);
    if (params.data_source) query.set('data_source', params.data_source);
    if (params.limit) query.set('limit', String(params.limit));

    const queryString = query.toString();
    return request<GeoJSONFeatureCollection>(`/api/hotspots/geojson${queryString ? `?${queryString}` : ''}`);
  },

  async getMetadata(dataSource: 'REAL' | 'SYNTHETIC' = 'REAL'): Promise<{ min_date: string; max_date: string }> {
    return request<{ min_date: string; max_date: string }>(`/api/hotspots/metadata?data_source=${dataSource}`);
  },

  async getHotspotDetail(id: string): Promise<HotspotDetail> {
    return request<HotspotDetail>(`/api/hotspots/${encodeURIComponent(id)}`);
  },

  async getHotspotPrediction(id: string): Promise<PredictionResponse> {
    return request<PredictionResponse>(`/api/hotspots/${encodeURIComponent(id)}/prediction`);
  },

  async getHotspotEvidence(id: string): Promise<EvidenceResponse> {
    return request<EvidenceResponse>(`/api/hotspots/${encodeURIComponent(id)}/evidence`);
  },

  async getHotspotRisk(id: string): Promise<RiskResponse> {
    return request<RiskResponse>(`/api/hotspots/${encodeURIComponent(id)}/risk`);
  },

  async getHotspotHistory(id: string): Promise<HistoryResponse> {
    return request<HistoryResponse>(`/api/hotspots/${encodeURIComponent(id)}/history`);
  },

  // Industrial Sites
  async getIndustrialSites(params: {
    min_lat?: number;
    max_lat?: number;
    min_lon?: number;
    max_lon?: number;
    facility_type?: string;
    page?: number;
    page_size?: number;
  } = {}): Promise<PaginatedResponse<IndustrialSite>> {
    const query = new URLSearchParams();
    if (params.min_lat !== undefined) query.set('min_lat', String(params.min_lat));
    if (params.max_lat !== undefined) query.set('max_lat', String(params.max_lat));
    if (params.min_lon !== undefined) query.set('min_lon', String(params.min_lon));
    if (params.max_lon !== undefined) query.set('max_lon', String(params.max_lon));
    if (params.facility_type) query.set('facility_type', params.facility_type);
    if (params.page) query.set('page', String(params.page));
    if (params.page_size) query.set('page_size', String(params.page_size));

    const queryString = query.toString();
    return request<PaginatedResponse<IndustrialSite>>(`/api/industrial-sites${queryString ? `?${queryString}` : ''}`);
  },

  async getIndustrialSiteDetail(id: string): Promise<IndustrialSite> {
    return request<IndustrialSite>(`/api/industrial-sites/${encodeURIComponent(id)}`);
  },

  // Analytics Intelligence
  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    return request<AnalyticsSummary>('/api/analytics/summary');
  },

  async getAnalyticsThermal(): Promise<any> {
    return request<any>('/api/analytics/thermal');
  },

  async getAnalyticsML(): Promise<any> {
    return request<any>('/api/analytics/ml');
  },

  async getAnalyticsGeospatial(): Promise<any> {
    return request<any>('/api/analytics/geospatial');
  },

  async getAnalyticsRisk(): Promise<any> {
    return request<any>('/api/analytics/risk');
  },

  async getAnalyticsInvestigations(): Promise<any> {
    return request<any>('/api/analytics/investigations');
  },

  // Intelligence Reports
  async getEventReport(eventId: string): Promise<any> {
    return request<any>(`/api/reports/event/${encodeURIComponent(eventId)}`);
  },

  async getSummaryReport(params: {
    report_type?: string;
    start_date?: string;
    end_date?: string;
  } = {}): Promise<any> {
    const query = new URLSearchParams();
    if (params.report_type) query.set('report_type', params.report_type);
    if (params.start_date) query.set('start_date', params.start_date);
    if (params.end_date) query.set('end_date', params.end_date);
    const queryString = query.toString();
    return request<any>(`/api/reports/summary${queryString ? `?${queryString}` : ''}`);
  },

  // Live NASA FIRMS Refresh
  async refreshLiveFirms(source: string = 'VIIRS_SNPP_NRT'): Promise<any> {
    return request<any>(`/api/ingestion/firms/live?country=IND&source=${encodeURIComponent(source)}`, {
      method: 'POST'
    });
  },

  // Investigations & Human Review
  async submitReview(hotspotId: string, payload: ReviewCreateRequest): Promise<ReviewResponse> {
    return request<ReviewResponse>(`/api/investigations/${encodeURIComponent(hotspotId)}/review`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getInvestigations(params: {
    review_status?: string;
    page?: number;
    page_size?: number;
  } = {}): Promise<PaginatedResponse<ReviewResponse>> {
    const query = new URLSearchParams();
    if (params.review_status) query.set('review_status', params.review_status);
    if (params.page) query.set('page', String(params.page));
    if (params.page_size) query.set('page_size', String(params.page_size));

    const queryString = query.toString();
    return request<PaginatedResponse<ReviewResponse>>(`/api/investigations${queryString ? `?${queryString}` : ''}`);
  },
};

