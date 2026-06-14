export function TypingIndicator() {
  return <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm dark:border-slate-800 dark:bg-slate-900"><span className="h-2 w-2 animate-bounce rounded-full bg-brand-500 [animation-delay:-0.3s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-brand-500 [animation-delay:-0.15s]" /><span className="h-2 w-2 animate-bounce rounded-full bg-brand-500" /><span className="ml-2">Retrieving authorized sources...</span></div>;
}
