interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className = "" }: CardProps) {
  return (
    <div className={`rounded-md border border-border bg-surface p-5 ${className}`}>
      {children}
    </div>
  );
}