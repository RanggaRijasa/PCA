import { createContext, type ReactNode, useContext, useState } from "react";

type ToastContextValue = { showToast: (message: string) => void };
const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState<string | null>(null);

  const showToast = (nextMessage: string) => {
    setMessage(nextMessage);
    window.setTimeout(() => setMessage(null), 2400);
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {message && (
        <div className="fixed bottom-5 left-1/2 z-50 -translate-x-1/2 rounded-xl bg-slate-950 px-4 py-3 text-sm font-medium text-white shadow-xl" role="status">
          {message}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used within ToastProvider");
  return context;
}

