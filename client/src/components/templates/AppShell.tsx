import type { ReactNode } from "react";

export function AppShell({ sidebar, children }: { sidebar: ReactNode; children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 bg-surface p-4">
        <p className="mb-6 px-1 text-sm font-bold">Onboarding assistant</p>
        {sidebar}
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
