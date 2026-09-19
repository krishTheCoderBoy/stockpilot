import { type InputHTMLAttributes, forwardRef } from "react";
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = "", id, ...props }, ref) => (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="text-sm text-text-muted">
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={id}
        className={`rounded-sm bg-surface border border-border px-3 py-2 text-sm text-text placeholder:text-text-muted/60 outline-none transition-colors focus:border-accent ${
          error ? "border-danger" : ""
        } ${className}`}
        {...props}
      />
      {error && <span className="text-xs text-danger">{error}</span>}
    </div>
  )
);
Input.displayName = "Input";