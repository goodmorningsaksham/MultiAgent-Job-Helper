'use client';

import { useEffect, useCallback } from 'react';

interface UseHotkeyOptions {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  callback: () => void;
  enabled?: boolean;
}

export function useHotkey({ key, ctrl, meta, shift, callback, enabled = true }: UseHotkeyOptions) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(
        (event.target as HTMLElement).tagName
      );
      if (isInput && !ctrl && !meta) return;

      const ctrlMatch = ctrl ? event.ctrlKey || event.metaKey : true;
      const metaMatch = meta ? event.metaKey : true;
      const shiftMatch = shift ? event.shiftKey : !event.shiftKey;

      if (event.key.toLowerCase() === key.toLowerCase() && ctrlMatch && metaMatch && shiftMatch) {
        event.preventDefault();
        callback();
      }
    },
    [key, ctrl, meta, shift, callback, enabled]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}
