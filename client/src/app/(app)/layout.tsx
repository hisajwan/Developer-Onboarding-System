import { redirect } from "next/navigation";
import { ProjectSwitcher } from "@/components/organisms/ProjectSwitcher";
import { AppShell } from "@/components/templates/AppShell";
import { NAV_ENTRIES } from "@/config/navigation";
import { getSession } from "@/lib/api/session";
import { AppBody } from "./AppBody";
import { AppNav } from "./AppNav";
import { ChatProvider } from "./ChatProvider";
import { ChatSessionProvider } from "./ChatSessionProvider";
import { ProjectDocsSidebar } from "./ProjectDocsSidebar";
import { ProjectDocumentsProvider } from "./ProjectDocumentsProvider";
import { ProjectProvider } from "./ProjectProvider";
import { SessionFooter } from "./SessionFooter";

export default async function AppLayout({ children }: LayoutProps<"/">) {
  const session = await getSession();
  if (!session) redirect("/login");

  return (
    <ProjectProvider initialProjectId={session.last_project_id}>
      <ProjectDocumentsProvider>
        <ChatSessionProvider>
          <ChatProvider>
            <AppShell
              projectSwitcher={<ProjectSwitcher />}
              nav={<AppNav entries={NAV_ENTRIES} />}
              docsPanel={<ProjectDocsSidebar />}
              footer={<SessionFooter username={session.username} />}
            >
              <AppBody>{children}</AppBody>
            </AppShell>
          </ChatProvider>
        </ChatSessionProvider>
      </ProjectDocumentsProvider>
    </ProjectProvider>
  );
}
