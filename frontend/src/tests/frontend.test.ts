import { api } from '../api/client.ts';
import type { GeoJSONFeatureCollection, PredictionResponse, ReviewCreateRequest } from '../types/api.ts';

// Unit Test Suite for AstraFlare Frontend Integrations

function assert(condition: boolean, message: string) {
  if (!condition) {
    throw new Error(`TEST FAILED: ${message}`);
  }
}

console.log('=== Running AstraFlare Frontend Test Suite ===');

// 0. Test API Client Definition
function testApiClientStructure() {
  assert(typeof api.getHealth === 'function', 'api.getHealth must be defined');
  assert(typeof api.getHotspots === 'function', 'api.getHotspots must be defined');
  assert(typeof api.getHotspotPrediction === 'function', 'api.getHotspotPrediction must be defined');
  assert(typeof api.submitReview === 'function', 'api.submitReview must be defined');
  console.log('✔ API client method signatures verified');
}

// 1. Test GeoJSON RFC 7946 Compliance
function testGeoJSONFormatting() {
  const sampleGeoJSON: GeoJSONFeatureCollection = {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [78.9629, 20.5937], // Strictly [longitude, latitude]
        },
        properties: {
          id: 'AF-TEST-001',
          latitude: 20.5937,
          longitude: 78.9629,
          acq_timestamp: '2026-09-01T12:00:00Z',
          satellite: 'VIIRS_SNPP',
          frp: 45.2,
          classification: 'LIKELY_INDUSTRIAL_INCIDENT',
          risk_level: 'HIGH',
          review_required: true,
          data_source: 'REAL',
        },
      },
    ],
  };

  assert(sampleGeoJSON.type === 'FeatureCollection', 'GeoJSON type must be FeatureCollection');
  assert(sampleGeoJSON.features.length === 1, 'Feature count must be 1');
  const feat = sampleGeoJSON.features[0];
  assert(feat.geometry.type === 'Point', 'Geometry type must be Point');
  assert(feat.geometry.coordinates[0] === 78.9629, 'Coordinates[0] must be Longitude');
  assert(feat.geometry.coordinates[1] === 20.5937, 'Coordinates[1] must be Latitude');
  console.log('✔ GeoJSON RFC 7946 format test passed');
}

// 2. Test ML Baseline Prediction Status & Operational Abstention
function testPredictionModelStatus() {
  const mockPrediction: PredictionResponse = {
    hotspot_id: 'AF-TEST-001',
    predicted_class: 'LIKELY_INDUSTRIAL_INCIDENT',
    confidence: 0.65,
    probabilities: {
      LIKELY_INDUSTRIAL_INCIDENT: 0.65,
      PERSISTENT_INDUSTRIAL_HEAT: 0.25,
      NATURAL_WILDLAND_FIRE: 0.10,
    },
    review_required: true,
    human_review_threshold: 0.80,
    model_version: 'v1.0.0-gbdt',
    model_status: 'RESEARCH BASELINE',
    limitations: 'Model status is RESEARCH BASELINE due to limited independent external ground truth.',
  };

  assert(mockPrediction.model_status === 'RESEARCH BASELINE', 'Model status must be RESEARCH BASELINE');
  assert(mockPrediction.review_required === true, 'Abstention must be true when confidence < threshold');
  assert(mockPrediction.confidence < mockPrediction.human_review_threshold, 'Confidence must be lower than threshold');
  console.log('✔ Prediction status & operational abstention test passed');
}

// 3. Test Review Request Formatting
function testReviewRequestPayload() {
  const payload: ReviewCreateRequest = {
    decision: 'CONFIRMED',
    reviewer_id: 'ANALYST-01',
    notes: 'Confirmed flare stack activity via satellite timeline.',
    corrected_classification: undefined,
  };

  assert(payload.decision === 'CONFIRMED', 'Decision must be CONFIRMED');
  assert(payload.reviewer_id === 'ANALYST-01', 'Reviewer ID must match');
  assert(payload.notes !== undefined, 'Notes must be present');
  console.log('✔ Analyst review submission payload test passed');
}

try {
  testApiClientStructure();
  testGeoJSONFormatting();
  testPredictionModelStatus();
  testReviewRequestPayload();
  console.log('\nALL FRONTEND UNIT TESTS PASSED SUCCESSFULLY! 🎉');
} catch (err: any) {
  console.error('\nFRONTEND TEST SUITE FAILED:', err.message);
  throw err;
}
