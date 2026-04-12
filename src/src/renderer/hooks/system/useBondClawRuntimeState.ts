import { useEffect, useState } from 'react';
import { ipcBridge } from '@/common';
import { getBondClawRuntimeSnapshot, type BondClawRuntimeSnapshot } from '@/common/config/bondclawRuntimeState';

export const useBondClawRuntimeState = (): BondClawRuntimeSnapshot => {
  const [runtimeState, setRuntimeState] = useState<BondClawRuntimeSnapshot>(getBondClawRuntimeSnapshot());

  useEffect(() => {
    let cancelled = false;

    const removeListener = ipcBridge.bondclaw.runtimeStateChanged.on((snapshot) => {
      if (!cancelled && snapshot) {
        setRuntimeState(snapshot);
      }
    });

    void ipcBridge.bondclaw.getRuntimeState
      .invoke()
      .then((snapshot) => {
        if (!cancelled && snapshot) {
          setRuntimeState(snapshot);
        }
      })
      .catch((error) => {
        console.warn('[BondClaw] Failed to load runtime state:', error);
      });

    return () => {
      cancelled = true;
      removeListener();
    };
  }, []);

  return runtimeState;
};
