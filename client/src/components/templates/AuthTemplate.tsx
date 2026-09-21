import type { ReactNode } from "react";
import { Heading } from "@/components/atoms/Heading";
import { APP_NAME } from "@/config/app";

export function AuthTemplate({ title, children }: { title: string; children: ReactNode }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-surface p-4">
      <div className="w-full max-w-sm rounded-xl bg-canvas p-8">
        <p className="mb-1 text-sm font-bold text-primary">{APP_NAME}</p>
        <Heading>{title}</Heading>
        <div className="mt-6">{children}</div>
      </div>
    </main>
  );
}
