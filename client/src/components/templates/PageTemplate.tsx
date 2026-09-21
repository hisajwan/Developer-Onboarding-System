import type { ReactNode } from "react";
import { Heading } from "@/components/atoms/Heading";

export function PageTemplate({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex h-full flex-col gap-6">
      <Heading>{title}</Heading>
      <div className="flex-1">{children}</div>
    </div>
  );
}
