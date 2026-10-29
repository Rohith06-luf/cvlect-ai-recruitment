import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: {
    value: string | number;
    isPositive?: boolean;
    neutral?: boolean;
    label?: string;
  };
  accentColor?: 'violet' | 'blue' | 'emerald' | 'amber';
  sublabel?: string;
  delay?: number;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon,
  trend,
  accentColor = 'violet',
  sublabel,
  delay = 0,
}) => {
  const colorMap = {
    violet: {
      iconBg: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
      glow: 'group-hover:border-violet-500/40',
      glowShadow: 'group-hover:shadow-[0_0_20px_rgba(124,58,237,0.15)]',
    },
    blue: {
      iconBg: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      glow: 'group-hover:border-blue-500/40',
      glowShadow: 'group-hover:shadow-[0_0_20px_rgba(59,130,246,0.15)]',
    },
    emerald: {
      iconBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      glow: 'group-hover:border-emerald-500/40',
      glowShadow: 'group-hover:shadow-[0_0_20px_rgba(16,185,129,0.15)]',
    },
    amber: {
      iconBg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      glow: 'group-hover:border-amber-500/40',
      glowShadow: 'group-hover:shadow-[0_0_20px_rgba(245,158,11,0.15)]',
    },
  }[accentColor];

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className={`group relative rounded-2xl p-6 glass-panel border border-white/10 transition-all duration-300 ${colorMap.glow} ${colorMap.glowShadow}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-400">{label}</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-white">{value}</span>
          </div>
          {sublabel && <p className="mt-1 text-xs text-slate-500">{sublabel}</p>}
        </div>
        <div className={`p-3 rounded-xl border ${colorMap.iconBg} shadow-inner`}>
          {icon}
        </div>
      </div>

      {trend && (
        <div className="mt-4 flex items-center gap-1.5 text-xs">
          {trend.neutral ? (
            <span className="inline-flex items-center text-slate-400">
              <Minus className="w-3.5 h-3.5 mr-0.5" />
              {trend.value}
            </span>
          ) : trend.isPositive ? (
            <span className="inline-flex items-center text-emerald-400 font-medium">
              <TrendingUp className="w-3.5 h-3.5 mr-0.5" />
              +{trend.value}
            </span>
          ) : (
            <span className="inline-flex items-center text-rose-400 font-medium">
              <TrendingDown className="w-3.5 h-3.5 mr-0.5" />
              -{trend.value}
            </span>
          )}
          {trend.label && <span className="text-slate-400">{trend.label}</span>}
        </div>
      )}
    </motion.div>
  );
};
