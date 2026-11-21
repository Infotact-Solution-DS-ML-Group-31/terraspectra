import React, { useEffect, useState } from 'react';
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
} from 'recharts';
import { api } from '../api/client';
import type {
  PcaCubeSummary,
  PcaExplainedVarianceResponse,
  PcaLoadingResponse,
  PcaSpatialScoresResponse,
  CubeId,
} from '../types/api';
import { LoadingState } from '../components/LoadingState';
import { ErrorBanner } from '../components/ErrorBanner';
import { Badge } from '../components/Badge';
import { DisclaimerBox } from '../components/DisclaimerBox';

const AVAILABLE_IDS: CubeId[] = ['2436', '3079'];

interface ChartTooltipPayload {
  active?: boolean;
  payload?: Array<{ color?: string; name?: string; value?: number }>;
  label?: string;
}

function VarianceTooltip({ active, payload, label }: ChartTooltipPayload) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 text-slate-300">{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} className="font-mono text-slate-100">
          {entry.name}: {((entry.value ?? 0) * 100).toFixed(2)}%
        </p>
      ))}
    </div>
  );
}

function colorForValue(value: number, min: number, max: number): string {
  if (!Number.isFinite(value)) return '#0f172a';
  const t = max === min ? 0.5 : (value - min) / (max - min);
  const hue = 220 - Math.max(0, Math.min(1, t)) * 180;
  return `hsl(${hue}, 75%, 58%)`;
}

export const PcaAnalysisView: React.FC = () => {
  const [selectedId, setSelectedId] = useState<CubeId>('2436');
  const [summary, setSummary] = useState<PcaCubeSummary | null>(null);
  const [variance, setVariance] = useState<PcaExplainedVarianceResponse | null>(null);
  const [loadings, setLoadings] = useState<PcaLoadingResponse | null>(null);
  const [spatial, setSpatial] = useState<PcaSpatialScoresResponse | null>(null);
  const [component, setComponent] = useState<'pc1' | 'pc2' | 'pc3'>('pc1');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    if (selectedId === '2973') {
      setSummary(null);
      setVariance(null);
      setLoadings(null);
      setSpatial(null);
      setError(null);
      setLoading(false);
      return () => {
        active = false;
      };
    }
    setLoading(true);
    setError(null);
    Promise.all([
      api.getPcaSummary(selectedId),
      api.getPcaExplainedVariance(selectedId),
      api.getPcaLoadings(selectedId),
      api.getPcaSpatialScores(selectedId, 64),
    ])
      .then(([nextSummary, nextVariance, nextLoadings, nextSpatial]) => {
        if (active) {
          setSummary(nextSummary);
          setVariance(nextVariance);
          setLoadings(nextLoadings);
          setSpatial(nextSpatial);
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
  }, [selectedId]);

  const spatialValues = spatial?.data
    .map((point) => point[component])
    .filter((value): value is number => value !== null) ?? [];
  const spatialMin = spatialValues.length ? Math.min(...spatialValues) : 0;
  const spatialMax = spatialValues.length ? Math.max(...spatialValues) : 1;
  const xLabel = variance?.spectral_axis.axis_type === 'wavelength_nm'
    ? 'Wavelength (nm)'
    : 'Zero-based band index';

  return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">PCA Analysis</h1>
        <p className="mt-1 text-sm text-slate-400">
          Independent exploratory PCA results from saved real-cube artifacts.
        </p>
      </div>

      {error && <ErrorBanner message={error} />}

      <div className="flex flex-wrap gap-2 items-center">
        {['2436', '2973', '3079'].map((id) => (
          <button
            key={id}
            onClick={() => setSelectedId(id as CubeId)}
            className={`rounded-md border px-4 py-2 text-sm font-mono font-semibold transition-colors ${
              selectedId === id
                ? 'border-cyan-500 bg-cyan-500/15 text-cyan-300'
                : 'border-slate-700 bg-slate-800/60 text-slate-400 hover:border-slate-600'
            }`}
          >
            {id}
          </button>
        ))}
        {summary && (
          <div className="ml-auto">
            <Badge
              label={summary.spectral_axis?.axis_type === 'wavelength_nm'
                ? 'Verified wavelengths'
                : 'Zero-based band indices'}
              variant={summary.spectral_axis?.axis_type === 'wavelength_nm' ? 'emerald' : 'amber'}
            />
          </div>
        )}
      </div>

      {selectedId === '2973' ? (
        <div className="rounded-lg border border-amber-800/60 bg-amber-950/20 p-6">
          <h2 className="font-semibold text-amber-200">PCA unavailable for image 2973</h2>
          <p className="mt-2 text-sm text-slate-400">
            No appropriate existing ROI mask was available, so no PCA result was fitted or fabricated.
          </p>
        </div>
      ) : loading ? (
        <LoadingState message={`Loading saved PCA artifacts for image ${selectedId}…`} />
      ) : variance && loadings && spatial ? (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            {variance.data.map((point) => (
              <div key={point.component} className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
                <p className="text-xs uppercase tracking-wider text-slate-500">{point.component}</p>
                <p className="mt-2 text-2xl font-semibold text-slate-100">
                  {(point.explained_variance_ratio * 100).toFixed(2)}%
                </p>
              </div>
            ))}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
              <h2 className="text-sm font-semibold text-slate-300">Explained variance</h2>
              <div className="mt-3 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={variance.data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="component" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <YAxis
                      tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                      tick={{ fill: '#94a3b8', fontSize: 10 }}
                      domain={[0, 1]}
                    />
                    <Tooltip content={<VarianceTooltip />} />
                    <Bar dataKey="explained_variance_ratio" name="Variance" fill="#22d3ee" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
              <h2 className="text-sm font-semibold text-slate-300">Cumulative explained variance</h2>
              <div className="mt-3 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={variance.data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="component" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <YAxis
                      tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                      tick={{ fill: '#94a3b8', fontSize: 10 }}
                      domain={[0, 1]}
                    />
                    <Tooltip content={<VarianceTooltip />} />
                    <Line
                      type="monotone"
                      dataKey="cumulative_explained_variance_ratio"
                      name="Cumulative"
                      stroke="#a78bfa"
                      strokeWidth={2}
                      dot
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-300">Spatial PCA scores</h2>
                <select
                  value={component}
                  onChange={(event) => setComponent(event.target.value as 'pc1' | 'pc2' | 'pc3')}
                  className="rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200"
                  aria-label="Spatial PCA component"
                >
                  <option value="pc1">PC1</option>
                  <option value="pc2">PC2</option>
                  <option value="pc3">PC3</option>
                </select>
              </div>
              <svg
                viewBox={`0 0 ${spatial.downsampled_width} ${spatial.downsampled_height}`}
                className="mt-3 aspect-square w-full rounded border border-slate-800 bg-slate-950"
                role="img"
                aria-label={`Downsampled ${component.toUpperCase()} spatial score map for image ${selectedId}`}
              >
                {spatial.data.map((point) => {
                  const value = point[component];
                  return (
                    <rect
                      key={`${point.row}-${point.column}`}
                      x={point.column}
                      y={point.row}
                      width={1}
                      height={1}
                      fill={value === null ? '#0f172a' : colorForValue(value, spatialMin, spatialMax)}
                    >
                      <title>
                        {value === null
                          ? 'Missing / outside valid region'
                          : `${component.toUpperCase()}: ${value.toFixed(4)}; valid pixels: ${point.valid_pixel_count}`}
                      </title>
                    </rect>
                  );
                })}
              </svg>
              <p className="mt-2 text-xs text-slate-500">
                Averaged into {spatial.downsampled_width} × {spatial.downsampled_height} blocks from the saved score map.
                Dark cells have no valid saved scores.
              </p>
            </div>

            <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
              <h2 className="text-sm font-semibold text-slate-300">Component loadings</h2>
              <div className="mt-3 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={loadings.data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="spectral_position"
                      tick={{ fill: '#94a3b8', fontSize: 9 }}
                      label={{ value: xLabel, position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 10 }}
                      tickFormatter={(value) => String(Math.round(value as number))}
                      interval={20}
                    />
                    <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="pc1" name="PC1" stroke="#22d3ee" dot={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="pc2" name="PC2" stroke="#a78bfa" dot={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="pc3" name="PC3" stroke="#fbbf24" dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {selectedId === '3079' && (
            <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
              <h2 className="text-sm font-semibold text-slate-300">Region-wise score distributions</h2>
              <p className="mt-2 text-sm text-slate-400">
                Structured region-wise distributions are not saved in the PCA artifact directory. The existing
                region score-distribution figure can show the historical result, but no values are fabricated or exposed here.
              </p>
            </div>
          )}
        </>
      ) : null}

      <DisclaimerBox
        items={[
          'PCA was fitted independently for each cube. Component scores and loadings must not be compared across cubes as if they share a basis.',
          'PCA components are exploratory mathematical components, not disease classes, healthy labels, or infected labels.',
          'Image 2436 has verified wavelengths from 397.32 to 1003.58 nm. Images 3079 and 2973 use or remain on band-index basis.',
          'Image 2973 has no appropriate ROI-based PCA result and is shown only as unavailable.',
          'No disease classification, forecasting, prediction, or clinical interpretation is claimed.',
        ]}
      />
    </div>
  );
};
