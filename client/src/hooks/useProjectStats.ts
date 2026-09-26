"use client";

import { useEffect, useState } from "react";
import { ApiError } from "@/lib/api/http";
import { getProjectStats } from "@/lib/api/stats";
import type { ProjectStats } from "@/types/stats";

/** The current project's Dashboard numbers and recent activity, reloaded when the project changes. */
export function useProjectStats(projectId: string | null) {
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!projectId) {
        setStats(null);
        return;
      }
      setIsLoading(true);
      setError(null);
      try {
        const data = await getProjectStats(projectId);
        if (!cancelled) setStats(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Could not load the dashboard.");
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  return { stats, isLoading, error };
}
