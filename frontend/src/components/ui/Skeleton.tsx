export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-sm bg-border/60 ${className}`}
    />
  );
}