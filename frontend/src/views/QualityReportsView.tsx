import React, { useEffect, useState } from 'react';
import { FileText, FileJson, ExternalLink } from 'lucide-react';
import { api } from '../api/client';
import type {
  QualityMetricsResponse,
  ReportSummary,
  ReportDetail,
  CubeId,
} from '../types/api';
import { LoadingState } from '../components/LoadingState';
import { ErrorBanner } from '../components/ErrorBanner';
import { MetricCard } from '../components/MetricCard';
import { Badge } from '../components/Badge';
import { DisclaimerBox } from '../components/DisclaimerBox';

const CUBE_IDS: CubeId[] = ['2436', '2973', '3079'];

export const QualityReportsView: React.FC = () => {
  const [selectedCube, setSelectedCube] = useState<CubeId>('3079');
  const [quality, setQuality] = useState<QualityMetricsResponse | null>(null);
  const [qualityLoading, setQualityLoading] = useState(false);

  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [reportsLoading, setReportsLoading] = useState(true);

  const [openReport, setOpenReport] = useState<ReportDetail | null>(null);
  const [reportLoading, setReportLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listReports()
      .then(setReports)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setReportsLoading(false));
  }, []);

  useEffect(() => {
    setQualityLoading(true);
    setQuality(null);
    api.getQuality(selectedCube)
      .then(setQuality)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setQualityLoading(false));
  }, [selectedCube]);

  function handleOpenReport(id: string) {
    setReportLoading(true);
    setOpenReport(null);
    api.getReport(id)
      .then(setOpenReport)
      .catch((e: unknown) => setError(String(e)))
      .finally(() => setReportLoading(false));
  }

  return (
    <div className="max-w-4xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Quality &amp; Reports</h1>
        <p className="mt-1 text-sm text-slate-400">
          Per-cube measurement quality audit and access to Phase B/C analytical reports.
        </p>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* ── Quality audit ───────────────────────── */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-400">
          Measurement Quality Audit
        </h2>
        <div className="flex gap-2 mb-4">
          {CUBE_IDS.map((id) => (
            <button
              key={id}
              onClick={() => { setSelectedCube(id); setError(null); }}
              className={`rounded-md border px-4 py-2 text-sm font-mono font-semibold transition-colors ${
                selectedCube === id
                  ? 'border-cyan-500 bg-cyan-500/15 text-cyan-300'
                  : 'border-slate-700 bg-slate-800/60 text-slate-400 hover:text-slate-200'
              }`}
            >
              {id}
            </button>
          ))}
        </div>

        {qualityLoading ? (
          <LoadingState message="Loading quality metrics…" />
        ) : quality ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <MetricCard
                label="NaN count"
                value={quality.nan_count.toLocaleString()}
                accent={quality.nan_count > 0 ? 'rose' : 'emerald'}
              />
              <MetricCard
                label="Inf count"
                value={quality.inf_count.toLocaleString()}
                accent={quality.inf_count > 0 ? 'rose' : 'emerald'}
              />
              <MetricCard
                label="Values > 1.0"
                value={quality.values_exceeding_1_count.toLocaleString()}
                sub={`${quality.values_exceeding_1_percentage.toFixed(2)}% of all pixels`}
                accent={quality.has_values_exceeding_1 ? 'amber' : 'emerald'}
              />
              <MetricCard
                label="Affected bands"
                value={quality.affected_bands_exceeding_1.length}
                sub="bands with exceedances"
                accent={quality.affected_bands_exceeding_1.length > 0 ? 'amber' : 'emerald'}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <MetricCard label="Min value" value={quality.min_value.toFixed(5)} accent="slate" />
              <MetricCard label="Max value" value={quality.max_value.toFixed(5)} accent="slate" />
            </div>

            {/* Warnings */}
            {quality.warnings.length > 0 && (
              <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4">
                <span className="text-xs font-semibold uppercase tracking-widest text-amber-400">
                  Warnings
                </span>
                <ul className="mt-2 space-y-1">
                  {quality.warnings.map((w, i) => (
                    <li key={i} className="text-xs text-amber-200/80">⚠ {w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Affected bands list */}
            {quality.affected_bands_exceeding_1.length > 0 && (
              <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-4">
                <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                  Bands with values &gt; 1.0
                </span>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {quality.affected_bands_exceeding_1.slice(0, 60).map((b) => (
                    <span
                      key={b}
                      className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-mono text-amber-300"
                    >
                      {b}
                    </span>
                  ))}
                  {quality.affected_bands_exceeding_1.length > 60 && (
                    <span className="text-xs text-slate-500">
                      +{quality.affected_bands_exceeding_1.length - 60} more
                    </span>
                  )}
                </div>
              </div>
            )}

            <DisclaimerBox items={quality.scientific_notes} />
          </div>
        ) : null}
      </section>

      {/* ── Reports ───────────────────────────────── */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-400">
          Analytical Reports
        </h2>
        {reportsLoading ? (
          <LoadingState message="Loading reports…" />
        ) : (
          <div className="space-y-2">
            {reports.map((r) => (
              <div
                key={r.id}
                className="flex items-start justify-between gap-4 rounded-lg border border-slate-700 bg-slate-900/40 px-4 py-3"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <span className="mt-0.5 shrink-0 text-slate-500">
                    {r.type === 'markdown' ? (
                      <FileText size={16} className="text-cyan-500" />
                    ) : (
                      <FileJson size={16} className="text-amber-500" />
                    )}
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-200 truncate">{r.title}</p>
                    <p className="text-xs text-slate-500 truncate">{r.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Badge label={r.type} variant={r.type === 'markdown' ? 'cyan' : 'amber'} size="xs" />
                  <button
                    onClick={() => handleOpenReport(r.id)}
                    className="flex items-center gap-1 rounded border border-slate-600 px-2 py-1 text-xs text-slate-400 hover:border-slate-500 hover:text-slate-200 transition-colors"
                  >
                    <ExternalLink size={12} />
                    View
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ── Report viewer modal/panel ──────────────────── */}
      {(reportLoading || openReport) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur p-4">
          <div className="relative w-full max-w-3xl max-h-[80vh] rounded-xl border border-slate-700 bg-slate-900 shadow-2xl flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-700 px-5 py-3 shrink-0">
              <span className="text-sm font-semibold text-slate-200">
                {openReport?.title ?? 'Loading report…'}
              </span>
              <button
                onClick={() => { setOpenReport(null); }}
                className="rounded px-2 py-1 text-xs text-slate-500 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              >
                ✕ Close
              </button>
            </div>
            <div className="overflow-auto p-5 flex-1">
              {reportLoading ? (
                <LoadingState message="Loading…" />
              ) : openReport?.type === 'markdown' ? (
                <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
                  {openReport.content as string}
                </pre>
              ) : (
                <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
                  {JSON.stringify(openReport?.content, null, 2)}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
