import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { api } from '../api/client';
import type { SpectralProfileResponse, CubeId } from '../types/api';
import { LoadingState } from '../components/LoadingState';
import { ErrorBanner } from '../components/ErrorBanner';
import { Badge } from '../components/Badge';
import { DisclaimerBox } from '../components/DisclaimerBox';

const CUBE_IDS: CubeId[] = ['2436', '2973', '3079'];

const CUBE_COLOR: Record<CubeId, string> = {
  '2436': '#22d3ee',
  '2973': '#fbbf24',
  '3079': '#a78bfa',
};

interface TooltipEntry {
  dataKey: string;
  color: string;
  value: number;
  name: string;
}

interface TooltipPayload {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string | number;
}

function makeTooltip(hasWl: boolean) {
  return function ChartTooltip({ active, payload, label }: TooltipPayload) {
    if (!active || !payload?.length) return null;
    return (
      <div className="rounded-md border border-slate-700 bg-slate-900/95 px-3 py-2 text-xs shadow-lg">
        <p className="font-mono text-slate-300 mb-1">
          {hasWl ? `${Number(label).toFixed(1)} nm` : `Band ${label}`}
        </p>
        {payload.map((entry) => (
          <div key={entry.dataKey} className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full" style={{ background: entry.color }} />
            <span className="text-slate-400">{entry.name}:</span>
            <span className="font-mono text-slate-100">{entry.value?.toFixed(4)}</span>
          </div>
        ))}
      </div>
    );
  };
}

export const SpectralAnalyticsView: React.FC = () => {
  const [selectedId, setSelectedId] = useState<CubeId>('2436');
  const [profile, setProfile] = useState<SpectralProfileResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setProfile(null);
    api.getSpectralProfile(selectedId)
      .then(setProfile)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [selectedId]);

  const chartData = profile?.data.map((pt) => ({
    x: pt.wavelength_nm ?? pt.band_index,
    mean: parseFloat(pt.mean.toFixed(5)),
    median: parseFloat(pt.median.toFixed(5)),
    ...(pt.q25 != null && { q25: parseFloat(pt.q25.toFixed(5)) }),
    ...(pt.q75 != null && { q75: parseFloat(pt.q75.toFixed(5)) }),
  })) ?? [];

  const hasWl = profile?.has_verified_wavelengths ?? false;
  const xLabel = hasWl ? 'Wavelength (nm)' : 'Band index (zero-based)';
  const color = CUBE_COLOR[selectedId];
  const TooltipContent = makeTooltip(hasWl);

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Spectral Analytics</h1>
        <p className="mt-1 text-sm text-slate-400">
          Whole-cube mean and median spectral profiles per image. Only image 2436 has verified ENVI
          wavelength calibration; 2973 and 3079 use zero-based band indices.
        </p>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Cube selector */}
      <div className="flex gap-2 items-center">
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
        {profile && (
          <div className="ml-auto flex items-center gap-2">
            <Badge
              label={hasWl ? '397–1004 nm calibrated' : 'Band index only (uncalibrated)'}
              variant={hasWl ? 'emerald' : 'amber'}
            />
          </div>
        )}
      </div>

      {loading ? (
        <LoadingState message="Loading spectral profile…" />
      ) : profile && chartData.length > 0 ? (
        <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-300">
              Image {selectedId} — Mean &amp; Median Spectral Profile
            </span>
            <span className="text-xs text-slate-500">{profile.total_bands} bands</span>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 4, right: 16, bottom: 24, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="x"
                  tickLine={false}
                  axisLine={{ stroke: '#334155' }}
                  tick={{ fill: '#94a3b8', fontSize: 10 }}
                  label={{ value: xLabel, position: 'insideBottom', offset: -12, fill: '#64748b', fontSize: 10 }}
                  tickFormatter={(v) => hasWl ? `${Math.round(v as number)}` : String(v)}
                  interval={hasWl ? 20 : 24}
                />
                <YAxis
                  tickLine={false}
                  axisLine={{ stroke: '#334155' }}
                  tick={{ fill: '#94a3b8', fontSize: 10 }}
                  tickFormatter={(v) => (v as number).toFixed(2)}
                  label={{ value: 'Value (NPZ)', angle: -90, position: 'insideLeft', offset: 10, fill: '#64748b', fontSize: 10 }}
                />
                <Tooltip content={<TooltipContent />} />
                <Legend
                  wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }}
                  formatter={(value) => <span style={{ color: '#94a3b8' }}>{value as string}</span>}
                />
                <Line
                  type="monotone"
                  dataKey="mean"
                  name="Mean"
                  stroke={color}
                  dot={false}
                  strokeWidth={1.8}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="median"
                  name="Median"
                  stroke={color}
                  dot={false}
                  strokeWidth={1.2}
                  strokeDasharray="4 2"
                  opacity={0.75}
                  isAnimationActive={false}
                />
                {chartData[0]?.q25 != null && (
                  <Line
                    type="monotone"
                    dataKey="q25"
                    name="Q25"
                    stroke={color}
                    dot={false}
                    strokeWidth={0.8}
                    opacity={0.4}
                    isAnimationActive={false}
                  />
                )}
                {chartData[0]?.q75 != null && (
                  <Line
                    type="monotone"
                    dataKey="q75"
                    name="Q75"
                    stroke={color}
                    dot={false}
                    strokeWidth={0.8}
                    opacity={0.4}
                    isAnimationActive={false}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
          {profile.scientific_notes.length > 0 && (
            <div className="mt-4">
              <DisclaimerBox items={profile.scientific_notes} />
            </div>
          )}
        </div>
      ) : null}

      <DisclaimerBox
        items={[
          'Wavelength values are only shown for image 2436 (Specim IQ ENVI-verified headers, 397.32–1003.58 nm).',
          'Images 2973 and 3079 have no verified wavelength metadata. Axis shows zero-based band indices 0–203.',
          'NPZ values are not laboratory-calibrated reflectance. Do not compare directly across instruments.',
          'The spectral profile for 3079 reflects the visible necrotic lesion ROI only, not the whole cube.',
        ]}
      />
    </div>
  );
};
