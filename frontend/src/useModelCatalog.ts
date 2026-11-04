import { useCallback, useEffect, useRef, useState } from 'react';
import type { ModelInventory } from './types';
import { request } from './useStudioBackend';

export function useModelCatalog() {
  const [catalog, setCatalog] = useState<ModelInventory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const mounted = useRef(true), version = useRef(0);
  const refresh = useCallback(async () => {
    const current = ++version.current;
    try {
      const next = await request<ModelInventory>('/api/models');
      if (mounted.current && current === version.current) { setCatalog(next); setError(null); }
      return next;
    } catch (cause) {
      if (mounted.current && current === version.current) setError(cause instanceof Error ? cause.message : 'Connection failed');
      return null;
    }
  }, []);
  useEffect(() => {
    mounted.current = true;
    let stopped = false, timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      const next = await refresh();
      if (!stopped) timer = setTimeout(() => void poll(), next?.models.some(m => ['queued','downloading','verifying','preparing'].includes(m.status)) ? 1000 : 5000);
    };
    void poll();
    return () => { stopped = true; mounted.current = false; clearTimeout(timer); };
  }, [refresh]);
  const action = async (id: string, operation: 'download' | 'cancel' | 'select') => {
    setBusy(id);
    try {
      await request(`/api/models/${id}/${operation}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      await refresh();
    } finally { if (mounted.current) setBusy(null); }
  };
  return { catalog, error, busy, refresh, action };
}
