import React, { useEffect, useMemo, useState } from 'react';
import {
  BarChart,
  Bar,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from 'recharts';
import { api } from '../api/client';
import type {
  ClusteringCubeSummary,
  ClusteringProfilesResponse,
  ClusteringSpatialMapResponse,
  CubeId,
} from '../types/api';
import { LoadingState } from '../components/LoadingState';
import { ErrorBanner } from '../components/ErrorBanner';
import { MetricCard } from '../components/MetricCard';
import { Badge } from '../components/Badge';
import { DisclaimerBox } from '../components/DisclaimerBox';

const CUBE_IDS: CubeId[] = ['2436', '2973', '3079'];
const K_VALUES = [2, 3, 4, 5] as const;

const CLUSTER_COLORS = [
  '#22d3ee', // cyan
  '#fbbf24', // amber
  '#f87171', // rose
  '#34d399', // emerald
  '#a78bfa', // violet
];

interface ProfileTooltipProps {
  active?: boolean;
  payload?: Array<{ color?: string; name?: string; value?: number }>;
  label?: string | number;
  isWavelength: boolean;
}

function ProfileTooltip({ active, payload, label, isWavelength }: ProfileTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-slate-700 bg-slate-900/95 px-3 py-2 text-xs shadow-lg">
      <p className="font-mono text-slate-300 mb-1">
        {isWavelength ? `${Number(label).toFixed(1)} nm` : `Band ${label}`}
      </p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ background: entry.color }} />
          <span className="text-slate-400">{entry.name}:</span>
          <span className="font-mono text-slate-100">{Number(entry.value ?? 0).toFixed(4)}</span>
        </div>
      ))}
    </div>
  );
}

export const ClusteringView: React.FC = () => {
  const [selectedId, setSelectedId] = useState<CubeId>('2436');
  const [selectedK, setSelectedK] = useState<number>(3);
  const [summary, setSummary] = useState<ClusteringCubeSummary | null>(null);
  const [profiles, setProfiles] = useState<ClusteringProfilesResponse | null>(null);
  const [spatialMap, setSpatialMap] = useState<ClusteringSpatialMapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (selectedId === '2973') {
      setSummary(null);
      setProfiles(null);
      setSpatialMap(null);
      setError(null);
      setLoading(false);
      return () => {
        active = false;
      };
    }

    setLoading(true);
    setError(null);
    Promise.all([
      api.getClusteringSummary(selectedId),
      api.getClusteringProfiles(selectedId, selectedK),
      api.getClusteringSpatialMap(selectedId, selectedK, 64),
    ])
      .then(([nextSummary, nextProfiles, nextMap]) => {
        if (active) {
          setSummary(nextSummary);
          setProfiles(nextProfiles);
          setSpatialMap(nextMap);
        }
      })
      .catch((e: unknown) => {
        if (active) setError(String(e));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [selectedId, selectedK]);

  const activeKResult = summary?.k_results?.[String(selectedK)] ?? null;
  const isWavelength = summary?.spectral_axis?.axis_type === 'wavelength_nm';
  const xLabel = summary?.spectral_axis?.axis_label ?? 'Spectral axis';

  const profileChartData = useMemo(() => {
    if (!profiles) return [];
    const axisVals = profiles.spectral_axis.values;
    return axisVals.map((xVal, idx) => {
      const row: Record<string, number> = { x: xVal };
      profiles.clusters.forEach((c) => {
        row[`C${c.cluster_id}`] = Number(c.mean_profile[idx]?.toFixed(5) ?? 0);
      });
      return row;
    });
  }, [profiles]);

  const silhouetteChartData = useMemo(() => {
    if (!summary) return [];
    return summary.k_values.map((k) => ({
      k: `K=${k}`,
      silhouette: summary.k_results[String(k)]?.silhouette_score ?? 0,
      seedAri: summary.k_results[String(k)]?.seed_stability_ari_mean ?? 0,
      spatialAri: summary.k_results[String(k)]?.spatial_block_stability_ari ?? 0,
    }));
  }, [summary]);

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">
          Exploratory Spectral Clustering (Phase F3)
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Independent per-cube standardized K-Means clustering on validated ROI pixels. Clusters
          reflect spectral grouping within one specimen and are not disease classes.
        </p>
      </div>

      {error && <ErrorBanner message={error} hint="Ensure Phase F3 artifacts are generated and the backend is running." />}

      {/* Cube & K selectors */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          {CUBE_IDS.map((id) => (
            <button
              key={id}
              onClick={() => { setSelectedId(id); setError(null); }}
              className={`rounded-md border px-4 py-2 text-sm font-mono font-semibold transition-colors ${
                selectedId === id
                  ? 'border-cyan-500 bg-cyan-500/15 text-cyan-300'
                  : 'border-slate-700 bg-slate-800/60 text-slate-400 hover:border-slate-600 hover:text-slate-200'
              }`}
            >
              {id}
            </button>
          ))}
        </div>

        {selectedId !== '2973' && (
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400 mr-1">Clusters (K):</span>
            {K_VALUES.map((k) => (
              <button
                key={k}
                onClick={() => setSelectedK(k)}
                className={`rounded-md border px-3 py-1.5 text-xs font-mono font-semibold transition-colors ${
                  selectedK === k
                    ? 'border-emerald-500 bg-emerald-500/15 text-emerald-300'
                    : 'border-slate-700 bg-slate-800/60 text-slate-400 hover:text-slate-200'
                }`}
              >
                K={k}
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedId === '2973' ? (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-6">
          <div className="flex items-center gap-2 mb-2">
            <Badge label="Skipped" variant="amber" />
            <span className="text-sm font-semibold text-slate-200">
              Image 2973 — No Validated ROI Mask Available
            </span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Image 2973 was excluded from Phase F3 clustering because no validated ROI mask exists and
            no ad-hoc segmentation was invented.
          </p>
        </div>
      ) : loading ? (
        <LoadingState message={`Loading Phase F3 clustering for image ${selectedId} (K=${selectedK})…`} />
      ) : summary && activeKResult ? (
        <>
          {/* Calibration & Config Badges */}
          <div className="flex flex-wrap gap-2">
            <Badge
              label={isWavelength ? 'Wavelengths: 397.32–1003.58 nm' : 'Zero-based band indices (0–203)'}
              variant={isWavelength ? 'emerald' : 'amber'}
            />
            <Badge label="StandardScaler + KMeans (seed=42)" variant="cyan" />
            <Badge label="Independent per-cube fit" variant="slate" />
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <MetricCard
              label="Valid ROI Pixels"
              value={(summary.valid_pixel_count ?? 0).toLocaleString()}
              sub={`Fit sample: ${(summary.fit_sample_count ?? 0).toLocaleString()} px`}
              accent="cyan"
            />
            <MetricCard
              label={`Silhouette (K=${selectedK})`}
              value={activeKResult.silhouette_score != null ? activeKResult.silhouette_score.toFixed(4) : 'N/A'}
              sub={`Subsampled (${activeKResult.silhouette_sample_size.toLocaleString()} px)`}
              accent="emerald"
            />
            <MetricCard
              label="Seed Stability ARI"
              value={activeKResult.seed_stability_ari_mean != null ? activeKResult.seed_stability_ari_mean.toFixed(4) : 'N/A'}
              sub="Across seeds 42, 101, 202"
              accent="slate"
            />
            <MetricCard
              label="Spatial Block ARI"
              value={activeKResult.spatial_block_stability_ari != null ? activeKResult.spatial_block_stability_ari.toFixed(4) : 'N/A'}
              sub="64×64 checkerboard split"
              accent="amber"
            />
          </div>

          {/* Spatial Map + Cluster Sizes */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {spatialMap && (
              <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                    Spatial Cluster Map (K={selectedK})
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">
                    {spatialMap.downsampled_width}×{spatialMap.downsampled_height} grid
                  </span>
                </div>
                <div
                  className="grid gap-0 rounded border border-slate-800 bg-slate-950 p-1 mx-auto"
                  style={{
                    gridTemplateColumns: `repeat(${spatialMap.downsampled_width}, minmax(0, 1fr))`,
                    maxWidth: '340px',
                    aspectRatio: '1 / 1',
                  }}
                >
                  {spatialMap.data.map((pt) => {
                    const bg =
                      pt.cluster_id !== null
                        ? CLUSTER_COLORS[pt.cluster_id % CLUSTER_COLORS.length]
                        : '#0f172a';
                    return (
                      <div
                        key={`${pt.row}-${pt.column}`}
                        title={
                          pt.cluster_id !== null
                            ? `(${pt.row},${pt.column}) Cluster ${pt.cluster_id}`
                            : 'Masked / background'
                        }
                        style={{ backgroundColor: bg }}
                      />
                    );
                  })}
                </div>
                <div className="mt-3 flex flex-wrap gap-3 justify-center">
                  {activeKResult.cluster_sizes.map((cs) => (
                    <div key={cs.cluster_id} className="flex items-center gap-1.5 text-xs text-slate-300">
                      <span
                        className="h-2.5 w-2.5 rounded-sm"
                        style={{ backgroundColor: CLUSTER_COLORS[cs.cluster_id % CLUSTER_COLORS.length] }}
                      />
                      <span className="font-mono">
                        C{cs.cluster_id}: {cs.percentage.toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Silhouette & Stability across K */}
            <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4 flex flex-col justify-between">
              <div>
                <span className="text-xs font-semibold uppercase tracking-widest text-slate-400 block mb-3">
                  Evaluation Metrics Across K=2..5
                </span>
                <div className="h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={silhouetteChartData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="k" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={{ stroke: '#334155' }} />
                      <YAxis domain={[0, 1]} tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={{ stroke: '#334155' }} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px' }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                      <Bar dataKey="silhouette" name="Silhouette" fill="#34d399" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                      <Bar dataKey="seedAri" name="Seed ARI" fill="#22d3ee" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                      <Bar dataKey="spatialAri" name="Spatial ARI" fill="#fbbf24" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Cluster size table */}
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-700 text-left text-slate-400">
                      <th className="py-1.5 pr-3">Cluster</th>
                      <th className="py-1.5 pr-3">Pixels</th>
                      <th className="py-1.5 pr-3">Share</th>
                      <th className="py-1.5">Mean SD</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {activeKResult.cluster_sizes.map((cs) => (
                      <tr key={cs.cluster_id}>
                        <td className="py-1.5 pr-3 font-mono text-slate-200">Cluster {cs.cluster_id}</td>
                        <td className="py-1.5 pr-3 font-mono text-slate-300">{cs.pixel_count.toLocaleString()}</td>
                        <td className="py-1.5 pr-3 font-mono text-slate-300">{cs.percentage.toFixed(2)}%</td>
                        <td className="py-1.5 font-mono text-slate-400">{cs.mean_within_cluster_std.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Cluster-wise Mean Spectral Profiles */}
          {profiles && profileChartData.length > 0 && (
            <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-300">
                  Image {selectedId} — Cluster Mean Spectral Profiles (K={selectedK})
                </span>
                <span className="text-xs text-slate-500">{xLabel}</span>
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={profileChartData} margin={{ top: 4, right: 16, bottom: 24, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="x"
                      tickLine={false}
                      axisLine={{ stroke: '#334155' }}
                      tick={{ fill: '#94a3b8', fontSize: 10 }}
                      tickFormatter={(v) => (isWavelength ? `${Math.round(Number(v))}` : String(v))}
                      interval={isWavelength ? 20 : 24}
                      label={{ value: xLabel, position: 'insideBottom', offset: -12, fill: '#64748b', fontSize: 10 }}
                    />
                    <YAxis
                      tickLine={false}
                      axisLine={{ stroke: '#334155' }}
                      tick={{ fill: '#94a3b8', fontSize: 10 }}
                      tickFormatter={(v) => Number(v).toFixed(2)}
                      label={{ value: 'Stored NPZ Value', angle: -90, position: 'insideLeft', offset: 10, fill: '#64748b', fontSize: 10 }}
                    />
                    <Tooltip content={<ProfileTooltip isWavelength={isWavelength} />} />
                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                    {profiles.clusters.map((c) => (
                      <Line
                        key={c.cluster_id}
                        type="monotone"
                        dataKey={`C${c.cluster_id}`}
                        name={`Cluster ${c.cluster_id}`}
                        stroke={CLUSTER_COLORS[c.cluster_id % CLUSTER_COLORS.length]}
                        dot={false}
                        strokeWidth={1.8}
                        isAnimationActive={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Post-hoc Exploratory ROI Comparison for Image 3079 */}
          {selectedId === '3079' && activeKResult.posthoc_roi_comparison && (
            <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                  Post-Hoc Exploratory Comparison vs Visual ROIs (K={selectedK})
                </span>
                <div className="flex gap-2">
                  <Badge
                    label={`ARI: ${activeKResult.posthoc_roi_comparison.adjusted_rand_index_vs_visual_roi ?? 'N/A'}`}
                    variant="violet"
                    size="xs"
                  />
                  <Badge
                    label={`NMI: ${activeKResult.posthoc_roi_comparison.normalized_mutual_info_vs_visual_roi ?? 'N/A'}`}
                    variant="cyan"
                    size="xs"
                  />
                </div>
              </div>
              <p className="text-xs text-amber-200/80">
                {activeKResult.posthoc_roi_comparison.note}
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-700 text-left text-slate-400">
                      <th className="py-2 pr-4">Visual ROI</th>
                      {Array.from({ length: selectedK }, (_, c) => (
                        <th key={c} className="py-2 pr-4 font-mono">Cluster {c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {Object.entries(activeKResult.posthoc_roi_comparison.contingency_counts).map(([roiName, counts]) => (
                      <tr key={roiName}>
                        <td className="py-2 pr-4 font-medium text-slate-300">
                          {roiName.replace(/_/g, ' ')}
                        </td>
                        {Array.from({ length: selectedK }, (_, c) => (
                          <td key={c} className="py-2 pr-4 font-mono text-slate-300">
                            {(counts[`cluster_${c}`] ?? 0).toLocaleString()}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <DisclaimerBox
            title="Experiment Configuration & Scientific Limitations"
            items={[
              summary.scientific_disclaimer,
              'Pixels are not independent biological samples; spatial autocorrelation inflates within-specimen stability.',
              'Visual ROI annotations for image 3079 are not laboratory-confirmed labels and were not used for fitting.',
              'No disease classification, pathogen identification, early detection, or forecasting is claimed.',
            ]}
          />
        </>
      ) : null}
    </div>
  );
};
