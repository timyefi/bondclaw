import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { ipcBridge } from '@/common';
import type { BondClawWorkspaceQuery, BondClawWorkspaceSnapshot } from '@/common/config/bondclawWorkspaceSnapshot';

const parseSearch = (search: string): BondClawWorkspaceQuery => {
  const params = new URLSearchParams(search);
  const role = params.get('role')?.trim() || undefined;
  const topic = params.get('topic')?.trim() || undefined;
  const caseId = params.get('case')?.trim() || undefined;
  return { role, topic, caseId };
};

export const useBondClawWorkspaceQuery = (): BondClawWorkspaceQuery => {
  const location = useLocation();
  return useMemo(() => parseSearch(location.search), [location.search]);
};

export const useBondClawWorkspaceSnapshot = (query: BondClawWorkspaceQuery) => {
  const [snapshot, setSnapshot] = useState<BondClawWorkspaceSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    void ipcBridge.bondclaw.getWorkspaceSnapshot
      .invoke(query)
      .then((nextSnapshot) => {
        if (!cancelled) {
          setSnapshot(nextSnapshot);
        }
      })
      .catch((nextError) => {
        if (!cancelled) {
          setError(nextError instanceof Error ? nextError.message : String(nextError));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [query.caseId, query.role, query.topic]);

  return {
    snapshot,
    loading,
    error,
    refresh: async () => {
      setLoading(true);
      setError('');
      try {
        const nextSnapshot = await ipcBridge.bondclaw.getWorkspaceSnapshot.invoke(query);
        setSnapshot(nextSnapshot);
      } catch (nextError) {
        setError(nextError instanceof Error ? nextError.message : String(nextError));
      } finally {
        setLoading(false);
      }
    },
  };
};
