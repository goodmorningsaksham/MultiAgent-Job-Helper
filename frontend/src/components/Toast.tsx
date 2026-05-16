'use client';

import { useEffect, useState, useCallback } from 'react';

interface ToastData {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

let addToastFn: ((toast: Omit<ToastData, 'id'>) => void) | null = null;

export function toast(message: string, type: 'success' | 'error' | 'info' = 'info') {
  addToastFn?.({ message, type });
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const addToast = useCallback((data: Omit<ToastData, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    setToasts((prev) => [...prev, { ...data, id }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  useEffect(() => {
    addToastFn = addToast;
    return () => { addToastFn = null; };
  }, [addToast]);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`px-4 py-3 rounded-xl shadow-lg border max-w-sm animate-in slide-in-from-right ${
            t.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
            t.type === 'error' ? 'bg-red-500/10 border-red-500/30 text-red-400' :
            'bg-primary-500/10 border-primary-500/30 text-primary-400'
          }`}
        >
          <p className="text-sm">{t.message}</p>
        </div>
      ))}
    </div>
  );
}
