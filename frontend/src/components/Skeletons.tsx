'use client';

export function CardSkeleton() {
  return (
    <div className="glass-card p-6 animate-pulse">
      <div className="h-4 bg-dark-700 rounded w-1/3 mb-3" />
      <div className="h-3 bg-dark-700/50 rounded w-full mb-2" />
      <div className="h-3 bg-dark-700/50 rounded w-2/3" />
    </div>
  );
}

export function GridSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

export function ListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 animate-pulse">
          <div className="w-10 h-10 bg-dark-700 rounded-xl" />
          <div className="flex-1">
            <div className="h-4 bg-dark-700 rounded w-1/3 mb-1.5" />
            <div className="h-3 bg-dark-700/50 rounded w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function TextBlockSkeleton() {
  return (
    <div className="animate-pulse space-y-2">
      <div className="h-3 bg-dark-700/50 rounded w-full" />
      <div className="h-3 bg-dark-700/50 rounded w-[90%]" />
      <div className="h-3 bg-dark-700/50 rounded w-[75%]" />
      <div className="h-3 bg-dark-700/50 rounded w-[85%]" />
    </div>
  );
}
