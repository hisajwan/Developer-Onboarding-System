import type { TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "w-full resize-y rounded-md border border-border px-3 py-2 text-sm outline-none focus:border-primary",
        className,
      )}
      {...props}
    />
  );
}
