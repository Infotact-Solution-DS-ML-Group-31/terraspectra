import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading…',
}) => (
  <div className="flex flex-col items-center justify-center gap-3 py-16 text-slate-400">
    <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
    <span className="text-sm">{message}</span>
  </div>
);
