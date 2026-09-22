import { redirect } from "next/navigation";
import { SidebarNav } from "@/components/organisms/SidebarNav";
import { AppShell } from "@/components/templates/AppShell";
import { NAV_ENTRIES } from "@/config/navigation";
import { getSession } from "@/lib/api/session";
import { AskDocsSidebar } from "./AskDocsSidebar";
import { SessionFooter } from "./SessionFooter";

export default async function AppLayout({ children }: LayoutProps<"/">) {
  const session = await getSession();
  if (!session) redirect("/login");

  return (
    <AppShell
      sidebar={<SidebarNav entries={NAV_ENTRIES} />}
      sidebarExtra={<AskDocsSidebar />}
      sidebarFooter={<SessionFooter username={session.username} />}
    >
      {children}
    </AppShell>
  );
}
