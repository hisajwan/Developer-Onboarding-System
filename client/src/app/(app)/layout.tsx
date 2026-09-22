import { redirect } from "next/navigation";
import { ProjectSwitcher } from "@/components/organisms/ProjectSwitcher";
import { AppShell } from "@/components/templates/AppShell";
import { NAV_ENTRIES } from "@/config/navigation";
import { getSession } from "@/lib/api/session";
import { AppBody } from "./AppBody";
import { AppNav } from "./AppNav";
import { ChatProvider } from "./ChatProvider";
import { ProjectDocsSidebar } from "./ProjectDocsSidebar";
import { ProjectProvider } from "./ProjectProvider";
import { SessionFooter } from "./SessionFooter";

export default async function AppLayout({ children }: LayoutProps<"/">) {
  const session = await getSession();
  if (!session) redirect("/login");

  return (
    <ProjectProvider initialProjectId={session.last_project_id}>
      <ChatProvider>
        <AppShell
          sidebarTop={<ProjectSwitcher />}
          sidebar={<AppNav entries={NAV_ENTRIES} />}
          sidebarExtra={<ProjectDocsSidebar />}
          sidebarFooter={<SessionFooter username={session.username} />}
        >
          <AppBody>{children}</AppBody>
        </AppShell>
      </ChatProvider>
    </ProjectProvider>
  );
}
