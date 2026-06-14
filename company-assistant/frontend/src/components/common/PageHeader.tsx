import type { ReactNode } from "react";

export function PageHeader({ title, description, actions }: { title: string; description: string; actions?: ReactNode }) {
  return <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center"><div><h1 className="text-2xl font-bold tracking-tight text-slate-950 dark:text-white">{title}</h1><p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p></div>{actions}</div>;
}

