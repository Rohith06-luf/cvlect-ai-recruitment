import React from 'react';

export const Skeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse rounded-lg bg-slate-800/60 ${className}`} />
);

export const CardSkeleton: React.FC = () => (
  <div className="glass-panel p-6 rounded-2xl border border-white/5 space-y-4">
    <div className="flex justify-between items-center">
      <Skeleton className="h-4 w-28" />
      <Skeleton className="h-10 w-10 rounded-xl" />
    </div>
    <Skeleton className="h-8 w-20" />
    <Skeleton className="h-3 w-36" />
  </div>
);

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <div className="glass-panel rounded-2xl p-4 border border-white/5 space-y-3">
    <div className="flex gap-4 pb-2 border-b border-white/5">
      <Skeleton className="h-4 w-1/4" />
      <Skeleton className="h-4 w-1/4" />
      <Skeleton className="h-4 w-1/4" />
      <Skeleton className="h-4 w-1/4" />
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex gap-4 py-3 items-center">
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-4 w-1/4" />
      </div>
    ))}
  </div>
);

export const ChartSkeleton: React.FC<{ height?: number }> = ({ height = 280 }) => (
  <div
    className="glass-panel rounded-2xl p-6 border border-white/5 flex flex-col justify-between"
    style={{ height }}
  >
    <div className="flex justify-between items-center">
      <Skeleton className="h-5 w-40" />
      <Skeleton className="h-4 w-20" />
    </div>
    <div className="flex items-end gap-3 h-44 pt-6">
      <Skeleton className="h-[40%] flex-1" />
      <Skeleton className="h-[75%] flex-1" />
      <Skeleton className="h-[55%] flex-1" />
      <Skeleton className="h-[90%] flex-1" />
      <Skeleton className="h-[65%] flex-1" />
      <Skeleton className="h-[80%] flex-1" />
    </div>
  </div>
);

export const DetailSkeleton: React.FC = () => (
  <div className="space-y-6">
    <div className="flex items-center gap-4">
      <Skeleton className="h-16 w-16 rounded-2xl" />
      <div className="space-y-2">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-32" />
      </div>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <CardSkeleton />
      <CardSkeleton />
      <CardSkeleton />
    </div>
    <div className="glass-panel rounded-2xl p-6 space-y-4">
      <Skeleton className="h-5 w-36" />
      <Skeleton className="h-20 w-full" />
    </div>
  </div>
);
