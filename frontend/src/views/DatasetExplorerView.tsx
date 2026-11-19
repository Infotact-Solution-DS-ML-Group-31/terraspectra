import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { DatasetSummary, DatasetMetadata, CubeId } from '../types/api';
import { LoadingState } from '../components/LoadingState';
import { ErrorBanner } from '../components/ErrorBanner';
import { Badge } from '../components/Badge';
import { MetricCard } from '../components/MetricCard';
import { DisclaimerBox } from '../components/DisclaimerBox';

const CUBE_IDS: CubeId[] = ['2436', '2973', '3079'];

export const DatasetExplorerView: React.FC = () => {
  const [selectedId, setSelectedId] = useState<CubeId>('2436');
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [metadata, setMetadata] = useState<DatasetMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [metaLoading, setMetaLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.listDatasets()
      .then(setDatasets)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setMetaLoading(true);
    setMetadata(null);
    setPreviewError(false);
    api.getMetadata(selectedId)
      .then(setMetadata)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setMetaLoading(false));
  }, [selectedId]);

  const selected = datasets.find((d) => d.image_id === selectedId);

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Dataset Explorer</h1>
        <p className="mt-1 text-sm text-slate-400">
          Browse the 3 locally available hyperspectral cubes. Only these cubes are accessible from
          the data/raw directory.
        </p>
      </div>

      {error && <ErrorBanner message={error} hint="Ensure the FastAPI backend is running on port 8000." />}

      {/* Cube selector */}
      <div className="flex gap-2">
        {CUBE_IDS.map((id) => (
          <button
            key={id}
            onClick={() => setSelectedId(id)}
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

      {loading ? (
        <LoadingState message="Loading datasets…" />
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Preview image */}
          <div className="rounded-lg border border-slate-700 bg-slate-900/60 overflow-hidden">
            <div className="border-b border-slate-700 px-4 py-2.5 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                False-colour Preview
              </span>
              <Badge
                label={
                  selectedId === '2436'
                    ? 'Wavelength-calibrated'
                    : 'Band-index only'
                }
                variant={selectedId === '2436' ? 'emerald' : 'amber'}
              />
            </div>
            <div className="aspect-square bg-slate-950 flex items-center justify-center">
              {previewError ? (
                <div className="text-center text-slate-500 text-sm px-6">
                  <p>Preview not available.</p>
                  <p className="text-xs mt-1">Run the preprocessing pipeline to generate preview PNGs.</p>
                </div>
              ) : (
                <img
                  src={api.previewUrl(selectedId)}
                  alt={`False-colour preview of image ${selectedId}`}
                  className="h-full w-full object-contain"
                  onError={() => setPreviewError(true)}
                  loading="lazy"
                />
              )}
            </div>
            <div className="px-4 py-2 text-[10px] text-slate-500">
              Rendered using 3-band PCA false-colour composite. Not a natural-colour photograph.
            </div>
          </div>

          {/* Cube summary + metadata */}
          <div className="space-y-4">
            {selected && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <MetricCard
                    label="Shape"
                    value={`${selected.shape[0]}×${selected.shape[1]}`}
                    sub={`${selected.spectral_bands} bands`}
                    accent="slate"
                  />
                  <MetricCard
                    label="File size"
                    value={`${selected.file_size_mb} MB`}
                    sub={selected.data_type}
                    accent="slate"
                  />
                </div>

                <div className="rounded-lg border border-slate-700 bg-slate-900/40 overflow-hidden">
                  <div className="border-b border-slate-700 px-4 py-2.5">
                    <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                      Acquisition Metadata
                    </span>
                  </div>
                  {metaLoading ? (
                    <div className="p-4"><LoadingState message="Loading metadata…" /></div>
                  ) : metadata ? (
                    <table className="w-full text-xs">
                      <tbody className="divide-y divide-slate-800">
                        {[
                          ['Pathogen', <span className="italic">{metadata.pathogen}</span>],
                          ['Replicate', metadata.replicate],
                          ['Sample', metadata.sample],
                          ['Plant part', metadata.part],
                          ['Acquisition date', metadata.date],
                          ['Integration time', `${metadata.integration_time_ms} ms`],
                          ['Weather', metadata.weather],
                          ['Plant ID', <span className="font-mono">{metadata.plant_id}</span>],
                          ['Organ ID', <span className="font-mono">{metadata.organ_id}</span>],
                          [
                            'Imaging distance',
                            metadata.imaging_distance_cm !== null
                              ? `${metadata.imaging_distance_cm} cm`
                              : <span className="text-slate-500">Not recorded</span>,
                          ],
                        ].map(([key, val], i) => (
                          <tr key={i} className="hover:bg-slate-800/30">
                            <td className="px-4 py-2 font-medium text-slate-500 w-40">{key}</td>
                            <td className="px-4 py-2 text-slate-300">{val as React.ReactNode}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p className="px-4 py-4 text-sm text-slate-500">No metadata available.</p>
                  )}
                </div>

                <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-3">
                  <p className="text-xs text-amber-200/70 leading-relaxed">
                    {metadata?.scientific_disclaimer ?? ''}
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      <DisclaimerBox
        items={[
          'Only 3 of 904 image IDs in metadata.tsv have locally available hyperspectral cubes.',
          'All 3 cubes are B. pseudocinerea. No Control or B. cinerea cubes are locally available.',
          'Preview images are false-colour composites for visualisation only.',
        ]}
      />
    </div>
  );
};
