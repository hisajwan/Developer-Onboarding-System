import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export type BadgeTone = "warning" | "danger" | "primary";

const TONES: Record<BadgeTone, string> = {
  warning: "bg-warning-soft text-warning",
  danger: "bg-danger-soft text-danger",
  primary: "bg-primary-soft text-primary",
};

export function Badge({ tone, children }: { tone: BadgeTone; children: ReactNode }) {
  return (
    <span className={cn("inline-block rounded-md px-3 py-1 text-xs font-bold", TONES[tone])}>
      {children}
    </span>
  );
}
