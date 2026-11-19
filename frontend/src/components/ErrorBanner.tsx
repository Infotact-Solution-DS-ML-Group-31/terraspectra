import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface ErrorBannerProps {
  message: string;
  hint?: string;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ message, hint }) => (
  <div className="flex items-start gap-3 rounded-lg border border-rose-500/30 bg-rose-500/10 p-4">
    <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-rose-400" />
    <div>
      <p className="text-sm font-medium text-rose-300">{message}</p>
      {hint && <p className="mt-1 text-xs text-rose-400/70">{hint}</p>}
    </div>
  </div>
);
