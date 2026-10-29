import React from 'react';
import { Check, X, AlertTriangle, Sparkles } from 'lucide-react';

export type SkillVariant = 'matched' | 'missing' | 'partial' | 'default' | 'violet';

interface SkillTagProps {
  name: string;
  variant?: SkillVariant;
  size?: 'sm' | 'md' | 'lg';
  onRemove?: () => void;
  className?: string;
}

export const SkillTag: React.FC<SkillTagProps> = ({
  name,
  variant = 'default',
  size = 'md',
  onRemove,
  className = '',
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'matched':
        return {
          bg: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300 shadow-emerald-950/20',
          icon: <Check className="w-3 h-3 text-emerald-400 stroke-[2.5]" />,
        };
      case 'missing':
        return {
          bg: 'bg-rose-500/15 border-rose-500/30 text-rose-300 shadow-rose-950/20',
          icon: <X className="w-3 h-3 text-rose-400 stroke-[2.5]" />,
        };
      case 'partial':
        return {
          bg: 'bg-amber-500/15 border-amber-500/30 text-amber-300 shadow-amber-950/20',
          icon: <AlertTriangle className="w-3 h-3 text-amber-400" />,
        };
      case 'violet':
        return {
          bg: 'bg-violet-500/15 border-violet-500/30 text-violet-300 shadow-violet-950/20',
          icon: <Sparkles className="w-3 h-3 text-violet-400" />,
        };
      case 'default':
      default:
        return {
          bg: 'bg-blue-500/15 border-blue-500/30 text-blue-300 shadow-blue-950/20',
          icon: null,
        };
    }
  };

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
    lg: 'text-sm px-3.5 py-1.5 gap-2',
  }[size];

  const config = getVariantStyles();

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border shadow-sm backdrop-blur-sm transition-all duration-150 hover:brightness-110 ${config.bg} ${sizeStyles} ${className}`}
    >
      {config.icon}
      <span>{name}</span>
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-0.5 text-slate-400 hover:text-white rounded-full p-0.5 hover:bg-white/10 transition-colors"
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </span>
  );
};
