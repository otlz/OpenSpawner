"use client";

import { useEffect, useRef } from "react";
import { api } from "@/lib/api";

/**
 * Sends periodic heartbeats to keep running containers alive.
 * Uses self-scheduling setTimeout to adapt interval from server response.
 *
 * @param runningTypes - Array of container types that are currently running.
 */
export function useHeartbeat(runningTypes: string[]) {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const intervalMs = useRef(1200000); // default 20 min
  const typesKey = [...runningTypes].sort().join(",");

  useEffect(() => {
    if (runningTypes.length === 0) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      return;
    }

    let cancelled = false;

    const sendAndReschedule = async () => {
      for (const type of runningTypes) {
        if (cancelled) return;
        const { data } = await api.heartbeat(type);
        if (data?.idle_timeout) {
          intervalMs.current = (data.idle_timeout * 1000) / 3;
        }
      }
      if (!cancelled) {
        timeoutRef.current = setTimeout(sendAndReschedule, intervalMs.current);
      }
    };

    // Send initial heartbeat immediately
    sendAndReschedule();

    return () => {
      cancelled = true;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [typesKey]); // eslint-disable-line react-hooks/exhaustive-deps
}
