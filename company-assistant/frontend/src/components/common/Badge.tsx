import type { ReactNode } from "react";

export function Badge({ children, tone = "slate" }: { children: ReactNode; tone?: "slate" | "green" | "amber" | "red" | "purple" }) {
  const styles = {
    slate: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200",
    green: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300",
    amber: "bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300",
    red: "bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300",
    purple: "bg-brand-50 text-brand-600 dark:bg-brand-500/20 dark:text-indigo-200",
  };
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${styles[tone]}`}>{children}</span>;
}

