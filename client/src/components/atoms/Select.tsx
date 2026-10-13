import type { SelectHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type Size = "sm" | "md";

const SIZES: Record<Size, string> = {
  sm: "px-2 py-1 text-xs",
  md: "px-2 py-1.5 text-sm",
};

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "size"> {
  size?: Size;
}

export function Select({ size = "sm", className, ...props }: SelectProps) {
  return (
    <select
      className={cn(
        "rounded-md border border-border bg-canvas outline-none focus:border-primary disabled:opacity-50",
        SIZES[size],
        className,
      )}
      {...props}
    />
  );
}
