"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/lib/api/http";
import { changePassword, getProfile, updateProfile } from "@/lib/api/profile";
import type { Profile } from "@/types/profile";

export function useProfile() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await getProfile();
        if (!cancelled) setProfile(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Could not load your profile.");
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const save = useCallback(async (firstName: string, lastName: string) => {
    const updated = await updateProfile(firstName, lastName);
    setProfile(updated);
    return updated;
  }, []);

  return { profile, isLoading, error, save, changePassword };
}
