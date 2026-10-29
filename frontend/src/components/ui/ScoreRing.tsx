import React from 'react';
import { motion } from 'framer-motion';

interface ScoreRingProps {
  score: number; // 0 to 100
  size?: 'sm' | 'md' | 'lg' | 'xl';
  label?: string;
  sublabel?: string;
  showGrade?: boolean;
  className?: string;
}

export const ScoreRing: React.FC<ScoreRingProps> = ({
  score,
  size = 'md',
  label,
  sublabel,
  showGrade = false,
  className = '',
}) => {
  const normalizedScore = Math.max(0, Math.min(100, Math.round(score)));

  // Color selection based on score threshold
  const getColor = (s: number) => {
    if (s >= 70) {
      return {
        stroke: '#10b981', // green
        text: 'text-emerald-400',
        bg: 'text-emerald-950/40',
        glow: 'rgba(16, 185, 129, 0.3)',
        grade: 'A',
      };
    }
    if (s >= 40) {
      return {
        stroke: '#f59e0b', // yellow/amber
        text: 'text-amber-400',
        bg: 'text-amber-950/40',
        glow: 'rgba(245, 158, 11, 0.3)',
        grade: 'B',
      };
    }
    return {
      stroke: '#ef4444', // red
      text: 'text-rose-400',
      bg: 'text-rose-950/40',
      glow: 'rgba(239, 68, 68, 0.3)',
      grade: 'C',
    };
  };

  const colorInfo = getColor(normalizedScore);

  const dimensions = {
    sm: { width: 56, strokeWidth: 5, fontSize: 'text-sm', labelSize: 'text-xs' },
    md: { width: 90, strokeWidth: 7, fontSize: 'text-xl font-bold', labelSize: 'text-xs' },
    lg: { width: 130, strokeWidth: 10, fontSize: 'text-3xl font-extrabold', labelSize: 'text-sm' },
    xl: { width: 180, strokeWidth: 12, fontSize: 'text-5xl font-black', labelSize: 'text-base' },
  }[size];

  const radius = (dimensions.width - dimensions.strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div className="relative flex items-center justify-center" style={{ width: dimensions.width, height: dimensions.width }}>
        <svg
          width={dimensions.width}
          height={dimensions.width}
          viewBox={`0 0 ${dimensions.width} ${dimensions.width}`}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={dimensions.width / 2}
            cy={dimensions.width / 2}
            r={radius}
            fill="transparent"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth={dimensions.strokeWidth}
          />
          {/* Progress circle */}
          <motion.circle
            cx={dimensions.width / 2}
            cy={dimensions.width / 2}
            r={radius}
            fill="transparent"
            stroke={colorInfo.stroke}
            strokeWidth={dimensions.strokeWidth}
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
            strokeLinecap="round"
            style={{
              filter: `drop-shadow(0 0 6px ${colorInfo.glow})`,
            }}
          />
        </svg>

        {/* Center score readout */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="flex items-baseline"
          >
            <span className={`${dimensions.fontSize} ${colorInfo.text} tracking-tight`}>
              {normalizedScore}
            </span>
            <span className="text-[10px] text-slate-400 font-medium ml-0.5">%</span>
          </motion.div>
          {showGrade && (
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Grade {colorInfo.grade}
            </span>
          )}
        </div>
      </div>

      {label && (
        <span className={`mt-2 font-medium text-slate-200 text-center ${dimensions.labelSize}`}>
          {label}
        </span>
      )}
      {sublabel && (
        <span className="text-xs text-slate-400 text-center">{sublabel}</span>
      )}
    </div>
  );
};
