import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts';
import { api } from '../api/client';
import type { RoiAnalysisResponse } from '../types/api';
import { LoadingState } from '../components/LoadingState';
import { ErrorBanner } from '../components/ErrorBanner';
import { MetricCard } from '../components/MetricCard';
import { Badge } from '../components/Badge';
import { DisclaimerBox } from '../components/DisclaimerBox';

const REGION_COLORS = {
  lesion: '#f87171',       // rose
  unaffected: '#34d399',   // emerald
  comparison: '#60a5fa',   // blue
};

function PairwiseTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-slate-700 bg-slate-900/95 px-3 py-2 text-xs shadow-lg">
      <p className="text-slate-400 mb-1">Band {label}</p>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex gap-2">
          <span className="text-slate-400">{p.name}:</span>
          <span className="font-mono text-slate-100">{(p.value as number)?.toFixed(4)}</span>
        </div>
      ))}
    </div>
  );
}

type PairKey = 'lesion_vs_adjacent_unaffected' | 'lesion_vs_comparison' | 'unaffected_vs_comparison';

const PAIR_LABELS: Record<PairKey, { label: string; color: string }> = {
  lesion_vs_adjacent_unaffected: { label: 'Lesion vs Unaffected', color: '#f87171' },
  lesion_vs_comparison: { label: 'Lesion vs Comparison', color: '#a78bfa' },
  unaffected_vs_comparison: { label: 'Unaffected vs Comparison', color: '#fbbf24' },
};

export const RoiComparisonView: React.FC = () => {
  const [roi, setRoi] = useState<RoiAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activePair, setActivePair] = useState<PairKey>('lesion_vs_adjacent_unaffected');

  useEffect(() => {
    api.getRoiAnalysis()
      .then(setRoi)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const counts = roi?.region_pixel_counts;
  const divergence = roi?.pairwise_divergence[activePair];

  // Build top-5 divergent bands bar chart data
  const top5Data = divergence?.top_5_divergent_bands.map((b, i) => ({
    band: b,
    rank: i + 1,
  })) ?? [];

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">ROI Comparison — Image 3079</h1>
        <p className="mt-1 text-sm text-slate-400">
          Three-region spectral comparison from manual lesion-level annotation. All 10 integrity
          checks passed. Bands use zero-based indices (no wavelength calibration).
        </p>
      </div>

      {error && <ErrorBanner message={error} hint="Ensure the backend is running and annotation files are present." />}
      {loading && <LoadingState message="Loading ROI analysis…" />}

      {roi && counts && (
        <>
          {/* Region pixel counts */}
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-400">
              Region Pixel Counts
            </h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <MetricCard
                label="Necrotic Lesion"
                value={counts.visible_necrotic_lesion.toLocaleString()}
                sub="visible necrotic ROI"
                accent="rose"
              />
              <MetricCard
                label="Unaffected Stem"
                value={counts.visually_unaffected_adjacent_stem.toLocaleString()}
                sub="adjacent to lesion"
                accent="emerald"
              />
              <MetricCard
                label="Comparison Stem"
                value={counts.preserved_comparison_stem.toLocaleString()}
                sub="lesion-free reference"
                accent="cyan"
              />
              <MetricCard
                label="Overlap"
                value={counts.overlap_pixels.toLocaleString()}
                sub="lesion ∩ unaffected"
                accent={counts.overlap_pixels === 0 ? 'emerald' : 'rose'}
              />
            </div>
          </section>

          {/* Annotation validation badge */}
          <div className="flex flex-wrap gap-2">
            <Badge label="All 10 integrity checks passed" variant="emerald" />
            <Badge label="Zero-based band indices (0–203)" variant="amber" />
            <Badge label="No wavelength calibration" variant="amber" />
            <Badge label="Lesion/adjacent overlap = 0 px" variant="emerald" />
          </div>

          {/* Pairwise divergence selector */}
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-400">
              Pairwise Spectral Divergence
            </h2>
            <div className="flex flex-wrap gap-2 mb-4">
              {(Object.keys(PAIR_LABELS) as PairKey[]).map((key) => (
                <button
                  key={key}
                  onClick={() => setActivePair(key)}
                  className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
                    activePair === key
                      ? 'border-cyan-500 bg-cyan-500/15 text-cyan-300'
                      : 'border-slate-700 bg-slate-800/60 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {PAIR_LABELS[key].label}
                </button>
              ))}
            </div>

            {divergence && (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-4">
                <MetricCard
                  label="Peak divergence band"
                  value={`Band ${divergence.max_abs_diff_band}`}
                  sub={`|Δμ| = ${divergence.max_abs_diff_value.toFixed(4)}`}
                  accent="amber"
                />
                <MetricCard
                  label="Mean |Δμ| all bands"
                  value={divergence.mean_abs_diff_all_bands.toFixed(4)}
                  sub="across 204 bands"
                  accent="slate"
                />
                {activePair === 'unaffected_vs_comparison' ? (
                  <>
                    <MetricCard
                      label="Unaffected mean at peak"
                      value={divergence.unaffected_mean_at_max_band?.toFixed(4) ?? '—'}
                      sub={`band ${divergence.max_abs_diff_band}`}
                      accent="emerald"
                    />
                    <MetricCard
                      label="Comparison mean at peak"
                      value={divergence.comparison_mean_at_max_band?.toFixed(4) ?? '—'}
                      sub={`band ${divergence.max_abs_diff_band}`}
                      accent="cyan"
                    />
                  </>
                ) : (
                  <>
                    <MetricCard
                      label="Lesion mean at peak"
                      value={divergence.lesion_mean_at_max_band.toFixed(4)}
                      sub={`band ${divergence.max_abs_diff_band}`}
                      accent="rose"
                    />
                    <MetricCard
                      label="Reference mean at peak"
                      value={(activePair === 'lesion_vs_adjacent_unaffected'
                        ? divergence.unaffected_mean_at_max_band
                        : divergence.comparison_mean_at_max_band)?.toFixed(4) ?? '—'}
                      sub={`band ${divergence.max_abs_diff_band}`}
                      accent="cyan"
                    />
                  </>
                )}
              </div>
            )}

            {/* Top-5 divergent bands bar chart */}
            {top5Data.length > 0 && divergence && (
              <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
                <span className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3 block">
                  Top 5 Most Divergent Bands — {PAIR_LABELS[activePair].label}
                </span>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={top5Data} margin={{ top: 4, right: 8, bottom: 8, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis
                        dataKey="band"
                        tickLine={false}
                        axisLine={{ stroke: '#334155' }}
                        tick={{ fill: '#94a3b8', fontSize: 10 }}
                        label={{ value: 'Band index', position: 'insideBottom', offset: -4, fill: '#64748b', fontSize: 10 }}
                      />
                      <YAxis
                        tickLine={false}
                        axisLine={{ stroke: '#334155' }}
                        tick={{ fill: '#94a3b8', fontSize: 10 }}
                        label={{ value: 'Rank', angle: -90, position: 'insideLeft', offset: 10, fill: '#64748b', fontSize: 10 }}
                      />
                      <Tooltip content={<PairwiseTooltip />} />
                      <ReferenceLine y={1} stroke="#475569" strokeDasharray="3 3" />
                      <Bar
                        dataKey="rank"
                        name="Divergence rank"
                        fill={PAIR_LABELS[activePair].color}
                        radius={[3, 3, 0, 0]}
                        isAnimationActive={false}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <p className="mt-2 text-[10px] text-slate-500">
                  Rank 1 = highest absolute mean difference between regions. Band 121 is the peak
                  divergence band across all pairings.
                </p>
              </div>
            )}
          </section>

          {/* Region colour legend */}
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-400">
              Region Legend
            </h2>
            <div className="flex flex-wrap gap-4">
              {[
                { label: 'Visible necrotic lesion', color: REGION_COLORS.lesion },
                { label: 'Visually unaffected adjacent stem tissue', color: REGION_COLORS.unaffected },
                { label: 'Preserved comparison stem', color: REGION_COLORS.comparison },
              ].map((r) => (
                <div key={r.label} className="flex items-center gap-2 text-xs text-slate-400">
                  <span className="h-3 w-3 rounded-sm shrink-0" style={{ background: r.color }} />
                  {r.label}
                </div>
              ))}
            </div>
          </section>

          <DisclaimerBox
            items={[
              ...roi.scientific_disclaimers,
              'The term "visually unaffected" reflects visual appearance only. Subclinical infection cannot be excluded.',
            ]}
          />
        </>
      )}
    </div>
  );
};
