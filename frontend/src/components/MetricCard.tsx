import React from 'react';
import { clsx } from 'clsx';

interface MetricCardProps {
  label: string;
  value: React.ReactNode;
  sub?: string;
  accent?: 'cyan' | 'amber' | 'emerald' | 'rose' | 'slate';
  className?: string;
}

const accentMap = {
  cyan: 'border-cyan-500/40 bg-cyan-500/5',
  amber: 'border-amber-500/40 bg-amber-500/5',
  emerald: 'border-emerald-500/40 bg-emerald-500/5',
  rose: 'border-rose-500/40 bg-rose-500/5',
  slate: 'border-slate-600/40 bg-slate-800/40',
} as const;

const valuColorMap = {
  cyan: 'text-cyan-300',
  amber: 'text-amber-300',
  emerald: 'text-emerald-300',
  rose: 'text-rose-300',
  slate: 'text-slate-200',
} as const;

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  sub,
  accent = 'slate',
  className,
}) => (
  <div
    className={clsx(
      'rounded-lg border p-4 flex flex-col gap-1',
      accentMap[accent],
      className
    )}
  >
    <span className="text-xs font-medium uppercase tracking-widest text-slate-400">{label}</span>
    <span className={clsx('text-2xl font-bold font-mono tabular-nums', valuColorMap[accent])}>
      {value}
    </span>
    {sub && <span className="text-xs text-slate-500">{sub}</span>}
  </div>
);
