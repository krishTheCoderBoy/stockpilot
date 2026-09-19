import { type HTMLMotionProps, motion } from "motion/react";
import { forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends HTMLMotionProps<"button"> {
  variant?: Variant;
}

const variantStyles: Record<Variant, string> = {
  primary: "bg-accent text-ink hover:bg-accent-muted",
  secondary: "bg-surface border border-border text-text hover:border-accent/50",
  ghost: "text-text-muted hover:text-text hover:bg-surface",
  danger: "bg-danger text-white hover:opacity-90",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", className = "", children, ...props }, ref) => (
    <motion.button
      ref={ref}
      whileTap={{ scale: 0.97 }}
      className={`inline-flex items-center gap-2 rounded-sm px-4 py-2 text-sm font-medium transition-colors duration-150 disabled:opacity-40 disabled:pointer-events-none ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </motion.button>
  )
);
Button.displayName = "Button";