import { ArrowUpRight } from "lucide-react";

const suggestions = ["Who approves an exception?", "What should I add to the team calendar?", "Show the most relevant policy section"];

export function FollowUpSuggestions({ onSelect, disabled }: { onSelect: (value: string) => void; disabled: boolean }) {
  return <section className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"><p className="mb-3 text-xs font-bold uppercase tracking-[0.14em] text-slate-400">Suggested follow-ups</p><div className="flex flex-wrap gap-2">{suggestions.map((suggestion) => <button key={suggestion} disabled={disabled} onClick={() => onSelect(suggestion)} className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-left text-xs font-semibold text-slate-600 transition hover:border-brand-500 hover:text-brand-600 disabled:opacity-50 dark:border-slate-700 dark:text-slate-300"><span>{suggestion}</span><ArrowUpRight className="h-3.5 w-3.5" /></button>)}</div></section>;
}

