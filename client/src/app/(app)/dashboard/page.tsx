"use client";

import { ActivityList } from "@/components/organisms/ActivityList";
import { StatsGrid } from "@/components/organisms/StatsGrid";
import { PageTemplate } from "@/components/templates/PageTemplate";
import { useProjectStats } from "@/hooks/useProjectStats";
import { useProjectContext } from "../ProjectProvider";

export default function DashboardPage() {
  const { currentProjectId, currentProject } = useProjectContext();
  const { stats, isLoading, error } = useProjectStats(currentProjectId);

  return (
    <PageTemplate title="Dashboard">
      <div className="flex flex-col gap-8">
        {currentProject && <p className="text-xs text-muted">Project: {currentProject.name}</p>}
        {error && (
          <p role="alert" className="text-xs text-danger">
            {error}
          </p>
        )}
        {!stats && isLoading && <p className="text-xs text-muted">Loading…</p>}
        {stats && (
          <>
            <StatsGrid
              stats={[
                { label: "Questions this week", value: stats.questions_this_week },
                { label: "Docs indexed", value: stats.documents_indexed },
                { label: "Reviews run", value: stats.reviews_total },
              ]}
            />
            <ActivityList items={stats.recent} />
          </>
        )}
      </div>
    </PageTemplate>
  );
}
