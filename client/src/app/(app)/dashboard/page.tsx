import { ActivityList } from "@/components/organisms/ActivityList";
import { StatsGrid } from "@/components/organisms/StatsGrid";
import { PageTemplate } from "@/components/templates/PageTemplate";
import { ACTIVITY, STATS } from "@/mocks/dashboard";

export default function DashboardPage() {
  return (
    <PageTemplate title="Dashboard">
      <div className="flex flex-col gap-8">
        <StatsGrid stats={STATS} />
        <ActivityList items={ACTIVITY} />
      </div>
    </PageTemplate>
  );
}
