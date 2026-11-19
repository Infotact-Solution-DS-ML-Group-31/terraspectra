import React from 'react';
import { Info } from 'lucide-react';

interface DisclaimerBoxProps {
  items: string[];
  title?: string;
}

export const DisclaimerBox: React.FC<DisclaimerBoxProps> = ({
  items,
  title = 'Scientific notes',
}) => {
  if (items.length === 0) return null;
  return (
    <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4">
      <div className="flex items-center gap-2 mb-2">
        <Info size={14} className="text-amber-400 shrink-0" />
        <span className="text-xs font-semibold uppercase tracking-widest text-amber-400">
          {title}
        </span>
      </div>
      <ul className="space-y-1">
        {items.map((note, i) => (
          <li key={i} className="text-xs text-amber-200/70 leading-relaxed">
            • {note}
          </li>
        ))}
      </ul>
    </div>
  );
};
