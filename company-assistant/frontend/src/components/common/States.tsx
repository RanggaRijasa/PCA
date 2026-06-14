import { AlertCircle, FileQuestion, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "./Button";

export function LoadingState({ label = "Loading local data..." }: { label?: string }) {
  return <div className="flex min-h-48 flex-col items-center justify-center gap-3 text-sm text-slate-500"><LoaderCircle className="h-6 w-6 animate-spin text-brand-500" /><span>{label}</span></div>;
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="flex min-h-48 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 p-8 text-center dark:border-slate-700 dark:bg-slate-900/60"><FileQuestion className="mb-3 h-8 w-8 text-slate-400" /><h3 className="font-semibold text-slate-900 dark:text-white">{title}</h3><p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>{action && <div className="mt-4">{action}</div>}</div>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200"><div className="flex items-start gap-3"><AlertCircle className="mt-0.5 h-5 w-5 shrink-0" /><div><p className="font-semibold">Something needs attention</p><p className="mt-1">{message}</p>{onRetry && <Button variant="danger" className="mt-3" onClick={onRetry}>Try again</Button>}</div></div></div>;
}

export function SkeletonRows({ count = 4 }: { count?: number }) {
  return <div className="space-y-3" aria-label="Loading"><span className="sr-only">Loading</span>{Array.from({ length: count }).map((_, index) => <div key={index} className="h-16 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />)}</div>;
}

