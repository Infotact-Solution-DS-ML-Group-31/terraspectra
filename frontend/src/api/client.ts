/**
 * Centralized API client for TerraSpectra backend.
 * Uses VITE_API_BASE_URL env variable (defaults to http://127.0.0.1:8000).
 */

import type {
  HealthResponse,
  DatasetSummary,
  DatasetMetadata,
  SpectralProfileResponse,
  RoiAnalysisResponse,
  QualityMetricsResponse,
  ReportSummary,
  ReportDetail,
  PcaCubeSummary,
  PcaExplainedVarianceResponse,
  PcaLoadingResponse,
  PcaSpatialScoresResponse,
  ClusteringCubeSummary,
  ClusteringProfilesResponse,
  ClusteringSpatialMapResponse,
} from '../types/api';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const BASE_URL: string = ((import.meta as any).env?.VITE_API_BASE_URL as string | undefined) ?? 'http://127.0.0.1:8000';

async function apiFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { Accept: 'application/json' },
    credentials: 'include',
  });
  if (!response.ok) {
    const text = await response.text().catch(() => 'Unknown error');
    throw new Error(`API ${response.status}: ${text}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: (): Promise<HealthResponse> =>
    apiFetch('/api/health'),

  listDatasets: (): Promise<DatasetSummary[]> =>
    apiFetch('/api/datasets'),

  getMetadata: (imageId: string): Promise<DatasetMetadata> =>
    apiFetch(`/api/datasets/${imageId}/metadata`),

  /** Returns a URL string (not fetched); use as <img src=…> */
  previewUrl: (imageId: string): string =>
    `${BASE_URL}/api/datasets/${imageId}/preview`,

  getSpectralProfile: (imageId: string): Promise<SpectralProfileResponse> =>
    apiFetch(`/api/datasets/${imageId}/spectral-profile`),

  getRoiAnalysis: (): Promise<RoiAnalysisResponse> =>
    apiFetch('/api/datasets/3079/roi-analysis'),

  getQuality: (imageId: string): Promise<QualityMetricsResponse> =>
    apiFetch(`/api/datasets/${imageId}/quality`),

  listReports: (): Promise<ReportSummary[]> =>
    apiFetch('/api/reports'),

  getReport: (reportId: string): Promise<ReportDetail> =>
    apiFetch(`/api/reports/${reportId}`),

  listPcaCubes: (): Promise<PcaCubeSummary[]> =>
    apiFetch('/api/pca/cubes'),

  getPcaSummary: (imageId: string): Promise<PcaCubeSummary> =>
    apiFetch(`/api/pca/${imageId}/summary`),

  getPcaExplainedVariance: (imageId: string): Promise<PcaExplainedVarianceResponse> =>
    apiFetch(`/api/pca/${imageId}/explained-variance`),

  getPcaLoadings: (imageId: string): Promise<PcaLoadingResponse> =>
    apiFetch(`/api/pca/${imageId}/loadings`),

  getPcaSpatialScores: (imageId: string, maxSize = 64): Promise<PcaSpatialScoresResponse> =>
    apiFetch(`/api/pca/${imageId}/spatial-scores?max_size=${maxSize}`),

  listClusteringCubes: (): Promise<ClusteringCubeSummary[]> =>
    apiFetch('/api/clustering/cubes'),

  getClusteringSummary: (imageId: string): Promise<ClusteringCubeSummary> =>
    apiFetch(`/api/clustering/${imageId}/summary`),

  getClusteringProfiles: (imageId: string, k = 3): Promise<ClusteringProfilesResponse> =>
    apiFetch(`/api/clustering/${imageId}/profiles?k=${k}`),

  getClusteringSpatialMap: (imageId: string, k = 3, maxSize = 64): Promise<ClusteringSpatialMapResponse> =>
    apiFetch(`/api/clustering/${imageId}/spatial-map?k=${k}&max_size=${maxSize}`),
};
