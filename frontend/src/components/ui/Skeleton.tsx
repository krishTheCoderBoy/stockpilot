export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse motion-reduce:animate-none rounded-sm bg-border/60 ${className}`}
    />
  );
}