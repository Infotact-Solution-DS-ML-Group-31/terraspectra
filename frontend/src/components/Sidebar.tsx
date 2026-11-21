import React from 'react';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  Database,
  LineChart,
  Layers,
  ClipboardList,
  Microscope,
  ScanLine,
} from 'lucide-react';
import type { ViewId } from '../types/api';

interface NavItem {
  id: ViewId;
  label: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: <LayoutDashboard size={18} /> },
  { id: 'dataset-explorer', label: 'Dataset Explorer', icon: <Database size={18} /> },
  { id: 'spectral-analytics', label: 'Spectral Analytics', icon: <LineChart size={18} /> },
  { id: 'roi-comparison', label: 'ROI Comparison', icon: <Layers size={18} /> },
  { id: 'pca-analysis', label: 'PCA Analysis', icon: <ScanLine size={18} /> },
  { id: 'quality-reports', label: 'Quality & Reports', icon: <ClipboardList size={18} /> },
];

interface SidebarProps {
  activeView: ViewId;
  onNavigate: (id: ViewId) => void;
  backendStatus: 'healthy' | 'degraded' | 'unknown';
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeView,
  onNavigate,
  backendStatus,
}) => {
  const statusColor = {
    healthy: 'bg-emerald-500',
    degraded: 'bg-amber-500',
    unknown: 'bg-slate-500',
  }[backendStatus];

  return (
    <aside className="flex h-screen w-56 shrink-0 flex-col border-r border-slate-800 bg-slate-900/80 backdrop-blur">
      {/* Logo */}
      <div className="flex items-center gap-2.5 border-b border-slate-800 px-4 py-5">
        <Microscope size={22} className="text-cyan-400" />
        <div>
          <span className="block text-sm font-bold tracking-tight text-slate-100">
            TerraSpectra
          </span>
          <span className="block text-[10px] font-medium uppercase tracking-widest text-slate-500">
            Hyperspectral Analytics
          </span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-4 space-y-0.5">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={clsx(
              'flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors',
              activeView === item.id
                ? 'bg-cyan-500/15 text-cyan-300'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            )}
          >
            <span className={activeView === item.id ? 'text-cyan-400' : 'text-slate-500'}>
              {item.icon}
            </span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* Backend health pill */}
      <div className="border-t border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className={clsx('h-2 w-2 rounded-full', statusColor)} />
          <span className="text-xs text-slate-500 capitalize">
            Backend {backendStatus}
          </span>
        </div>
        <p className="mt-0.5 text-[10px] text-slate-600">FastAPI · port 8000</p>
      </div>
    </aside>
  );
};
