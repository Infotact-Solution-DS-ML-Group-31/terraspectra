import React from 'react';
import { clsx } from 'clsx';

interface BadgeProps {
  label: string;
  variant?: 'cyan' | 'amber' | 'emerald' | 'rose' | 'slate' | 'violet';
  size?: 'sm' | 'xs';
}

const variantMap = {
  cyan: 'bg-cyan-500/20 text-cyan-300 ring-1 ring-cyan-500/30',
  amber: 'bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/30',
  emerald: 'bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/30',
  rose: 'bg-rose-500/20 text-rose-300 ring-1 ring-rose-500/30',
  slate: 'bg-slate-700/50 text-slate-300 ring-1 ring-slate-600/40',
  violet: 'bg-violet-500/20 text-violet-300 ring-1 ring-violet-500/30',
};

export const Badge: React.FC<BadgeProps> = ({
  label,
  variant = 'slate',
  size = 'sm',
}) => (
  <span
    className={clsx(
      'inline-flex items-center rounded-full font-medium',
      variantMap[variant],
      size === 'xs' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-0.5 text-xs'
    )}
  >
    {label}
  </span>
);
