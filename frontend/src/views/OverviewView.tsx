import React from 'react';
import { AlertTriangle, CheckCircle, Database, Layers, TestTube2, TrendingUp } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { Badge } from '../components/Badge';
import { DisclaimerBox } from '../components/DisclaimerBox';

export const OverviewView: React.FC = () => {
  return (
    <div className="max-w-4xl space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">
          TerraSpectra — Hyperspectral Analytics Platform
        </h1>
        <p className="mt-2 text-sm text-slate-400 leading-relaxed max-w-2xl">
          An exploratory research platform for analysing hyperspectral imaging data of tomato plants
          infected with <em>Botrytis pseudocinerea</em>. This platform does not train a disease
          classifier or produce predictive models.
        </p>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <MetricCard
          label="Metadata records"
          value="904"
          sub="in metadata.tsv"
          accent="cyan"
        />
        <MetricCard
          label="Unique plants"
          value="49"
          sub="biological replicates"
          accent="emerald"
        />
        <MetricCard
          label="Local cubes"
          value="3"
          sub="of 904 image IDs"
          accent="amber"
        />
        <MetricCard
          label="Spectral bands"
          value="204"
          sub="per cube (512 × 512)"
          accent="slate"
        />
      </div>

      {/* Dataset composition */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-400">
          Dataset Composition
        </h2>
        <div className="rounded-lg border border-slate-700 bg-slate-900/60 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700 text-left">
                <th className="px-4 py-2.5 font-medium text-slate-400 text-xs uppercase tracking-wider">Image ID</th>
                <th className="px-4 py-2.5 font-medium text-slate-400 text-xs uppercase tracking-wider">Pathogen</th>
                <th className="px-4 py-2.5 font-medium text-slate-400 text-xs uppercase tracking-wider">Replicate</th>
                <th className="px-4 py-2.5 font-medium text-slate-400 text-xs uppercase tracking-wider">Wavelengths</th>
                <th className="px-4 py-2.5 font-medium text-slate-400 text-xs uppercase tracking-wider">Phase A ROI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              <tr className="hover:bg-slate-800/40">
                <td className="px-4 py-2.5 font-mono text-cyan-300">2436</td>
                <td className="px-4 py-2.5 text-slate-300 text-xs italic">B. pseudocinerea</td>
                <td className="px-4 py-2.5 text-slate-400">Rep 1</td>
                <td className="px-4 py-2.5"><Badge label="397–1004 nm" variant="emerald" /></td>
                <td className="px-4 py-2.5"><Badge label="Leaf ROI" variant="cyan" /></td>
              </tr>
              <tr className="hover:bg-slate-800/40">
                <td className="px-4 py-2.5 font-mono text-cyan-300">2973</td>
                <td className="px-4 py-2.5 text-slate-300 text-xs italic">B. pseudocinerea</td>
                <td className="px-4 py-2.5 text-slate-400">Rep 3</td>
                <td className="px-4 py-2.5"><Badge label="Band index only" variant="amber" /></td>
                <td className="px-4 py-2.5"><Badge label="Whole cube" variant="slate" /></td>
              </tr>
              <tr className="hover:bg-slate-800/40">
                <td className="px-4 py-2.5 font-mono text-cyan-300">3079</td>
                <td className="px-4 py-2.5 text-slate-300 text-xs italic">B. pseudocinerea</td>
                <td className="px-4 py-2.5 text-slate-400">Rep 4</td>
                <td className="px-4 py-2.5"><Badge label="Band index only" variant="amber" /></td>
                <td className="px-4 py-2.5"><Badge label="Lesion-level 3-ROI" variant="violet" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* ML feasibility summary */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-400">
          ML Feasibility Assessment
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {[
            {
              icon: <AlertTriangle size={16} className="text-rose-400" />,
              title: 'Single-class pathogen bias',
              body: 'All 3 locally available cubes are B. pseudocinerea. No Control or B. cinerea cubes are available locally. Classification across pathogen classes is not feasible without additional data.',
              color: 'border-rose-500/20 bg-rose-500/5',
            },
            {
              icon: <AlertTriangle size={16} className="text-amber-400" />,
              title: 'Severe data imbalance',
              body: '904 records across 49 plants but only 3 hyperspectral cubes are locally available, limiting generalisation. Pseudo-replication risk exists across repeated measurements of the same plant.',
              color: 'border-amber-500/20 bg-amber-500/5',
            },
            {
              icon: <CheckCircle size={16} className="text-emerald-400" />,
              title: 'Lesion-level annotation complete',
              body: 'Image 3079 has validated 3-region manual lesion annotation: necrotic lesion (4,137 px), visually unaffected adjacent stem (18,661 px), and preserved comparison stem (30,532 px).',
              color: 'border-emerald-500/20 bg-emerald-500/5',
            },
            {
              icon: <TrendingUp size={16} className="text-cyan-400" />,
              title: 'Spectral contrast confirmed',
              body: 'Peak pairwise divergence at band index 121 (|Δμ| ≈ 0.251 vs unaffected, ≈ 0.298 vs comparison). Values > 1.0 in comparison stem (bands 124–171) attributed to possible specular reflections.',
              color: 'border-cyan-500/20 bg-cyan-500/5',
            },
          ].map((card) => (
            <div
              key={card.title}
              className={`rounded-lg border p-4 ${card.color}`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                {card.icon}
                <span className="text-sm font-semibold text-slate-200">{card.title}</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{card.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Phase progress */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-400">
          Research Phases
        </h2>
        <div className="space-y-2">
          {[
            { label: 'Phase A — Lesion annotation & spectral extraction', done: true, icon: <Layers size={14} /> },
            { label: 'Phase B — Spectral robustness & reproducibility analysis', done: true, icon: <TestTube2 size={14} /> },
            { label: 'Phase C — Dataset-wide biological assessment & ML feasibility', done: true, icon: <Database size={14} /> },
            { label: 'Phase D — Interactive analytics platform (this UI)', done: true, icon: <TrendingUp size={14} /> },
          ].map((phase) => (
            <div
              key={phase.label}
              className="flex items-center gap-3 rounded-md border border-slate-800 bg-slate-900/40 px-4 py-2.5"
            >
              <span className={phase.done ? 'text-emerald-400' : 'text-slate-600'}>{phase.icon}</span>
              <span className={`text-sm ${phase.done ? 'text-slate-300' : 'text-slate-500'}`}>
                {phase.label}
              </span>
              {phase.done && (
                <Badge label="Complete" variant="emerald" size="xs" />
              )}
            </div>
          ))}
        </div>
      </section>

      <DisclaimerBox
        title="Platform limitations"
        items={[
          'This platform is for exploratory analysis only. No disease classifications or model predictions are made.',
          'Only 3 of 904 image records have locally available hyperspectral cubes.',
          'Wavelength calibration is available only for image 2436. Images 2973 and 3079 use zero-based band indices.',
          'NPZ values must not be assumed to be calibrated laboratory reflectance.',
        ]}
      />
    </div>
  );
};
