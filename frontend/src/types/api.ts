/**
 * TypeScript interfaces matching TerraSpectra backend API schemas.
 * All types are strictly derived from FastAPI Pydantic models.
 */

// ─────────────────────────── Health ───────────────────────────────────────
export interface HealthResponse {
  status: 'healthy' | 'degraded';
  version: string;
  platform: string;
  timestamp: string;
  local_cubes_available: number;
  metadata_records: number;
}

// ─────────────────────────── Datasets ─────────────────────────────────────
export interface DatasetSummary {
  image_id: string;
  shape: [number, number, number];
  spectral_bands: number;
  data_type: string;
  file_size_mb: number;
  calibration_status: string;
  has_wavelength_calibration: boolean;
  pathogen: string;
  replicate: number;
  sample: number;
  part: string;
  date: string;
}

export interface DatasetMetadata {
  image_id: string;
  replicate: number;
  pathogen: string;
  sample: number;
  part: string;
  date: string;
  imaging_distance_cm: number | null;
  integration_time_ms: number;
  weather: string;
  plant_id: string;
  organ_id: string;
  calibration_status: string;
  verified_wavelengths: boolean;
  scientific_disclaimer: string;
}

// ─────────────────────────── Spectral ─────────────────────────────────────
export interface SpectralBandPoint {
  band_index: number;
  wavelength_nm: number | null;
  mean: number;
  median: number;
  std: number | null;
  q25: number | null;
  q75: number | null;
}

export interface SpectralProfileResponse {
  image_id: string;
  spectral_axis: 'wavelength_nm' | 'zero_based_band_indices';
  total_bands: number;
  has_verified_wavelengths: boolean;
  data: SpectralBandPoint[];
  scientific_notes: string[];
}

// ─────────────────────────── ROI ──────────────────────────────────────────
export interface RoiPixelCounts {
  visible_necrotic_lesion: number;
  visually_unaffected_adjacent_stem: number;
  preserved_comparison_stem: number;
  lesion_bearing_stem_total: number;
  unannotated_stem_margin: number;
  overlap_pixels: number;
}

export interface DivergenceStats {
  max_abs_diff_band: number;
  max_abs_diff_value: number;
  lesion_mean_at_max_band: number;
  comparison_mean_at_max_band?: number;
  unaffected_mean_at_max_band?: number;
  mean_abs_diff_all_bands: number;
  top_5_divergent_bands: number[];
}

export interface RoiAnalysisResponse {
  image_id: string;
  spectral_axis: string;
  wavelength_calibration: string;
  region_pixel_counts: RoiPixelCounts;
  pairwise_divergence: Record<string, DivergenceStats>;
  scientific_disclaimers: string[];
}

// ─────────────────────────── Quality ──────────────────────────────────────
export interface QualityMetricsResponse {
  image_id: string;
  nan_count: number;
  inf_count: number;
  min_value: number;
  max_value: number;
  values_exceeding_1_count: number;
  values_exceeding_1_percentage: number;
  has_values_exceeding_1: boolean;
  affected_bands_exceeding_1: number[];
  warnings: string[];
  scientific_notes: string[];
}

// ─────────────────────────── Reports ──────────────────────────────────────
export interface ReportSummary {
  id: string;
  title: string;
  type: 'json' | 'markdown';
  description: string;
  filename: string;
}

export interface ReportDetail {
  id: string;
  title: string;
  type: 'json' | 'markdown';
  content: string | Record<string, unknown>;
}

// ─────────────────────────── App State ────────────────────────────────────
export type ViewId =
  | 'overview'
  | 'dataset-explorer'
  | 'spectral-analytics'
  | 'roi-comparison'
  | 'pca-analysis'
  | 'quality-reports';

export type CubeId = '2436' | '2973' | '3079';

export interface PcaSpectralAxis {
  axis_type: 'wavelength_nm' | 'zero_based_band_index';
  axis_label: string;
  values: Array<number>;
  calibration_status: string;
}

export interface PcaCubeSummary {
  image_id: string;
  status: 'analyzed' | 'skipped';
  available: boolean;
  spectral_axis?: PcaSpectralAxis;
  spectral_features_per_pixel?: number;
  valid_pixel_count?: number;
  fit_sample_count?: number;
  cumulative_explained_variance_ratio?: number;
  region_distributions_available: boolean;
  region_distributions_reason?: string;
  scientific_disclaimer: string;
}

export interface PcaExplainedVariancePoint {
  component: 'PC1' | 'PC2' | 'PC3';
  explained_variance_ratio: number;
  cumulative_explained_variance_ratio: number;
}

export interface PcaExplainedVarianceResponse {
  image_id: string;
  independent_fit: boolean;
  cumulative_explained_variance_ratio: number;
  data: PcaExplainedVariancePoint[];
  spectral_axis: PcaSpectralAxis;
}

export interface PcaLoadingPoint {
  spectral_position: number;
  pc1: number;
  pc2: number;
  pc3: number;
}

export interface PcaLoadingResponse {
  image_id: string;
  independent_fit: boolean;
  spectral_axis: PcaSpectralAxis;
  data: PcaLoadingPoint[];
}

export interface PcaSpatialPoint {
  row: number;
  column: number;
  pc1: number | null;
  pc2: number | null;
  pc3: number | null;
  valid_pixel_count: number;
}

export interface PcaSpatialScoresResponse {
  image_id: string;
  independent_fit: boolean;
  width: number;
  height: number;
  downsampled_width: number;
  downsampled_height: number;
  data: PcaSpatialPoint[];
  spectral_axis: PcaSpectralAxis;
}
