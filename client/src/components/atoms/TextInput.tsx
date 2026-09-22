import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export function TextInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "w-full rounded-md border border-border px-3 py-2 text-sm outline-none focus:border-primary",
        "disabled:cursor-not-allowed disabled:border-border disabled:bg-surface disabled:text-muted",
        className,
      )}
      {...props}
    />
  );
}
