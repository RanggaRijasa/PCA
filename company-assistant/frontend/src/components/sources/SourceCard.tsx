import { ChevronDown, ChevronUp, FileText, LockKeyhole } from "lucide-react";
import { useState } from "react";
import { useAuthenticatedUser } from "../../context/AuthContext";
import type { SourceCitation } from "../../types";
import { Badge } from "../common/Badge";

export function SourceCard({ source }: { source: SourceCitation }) {
  const [expanded, setExpanded] = useState(false);
  const currentUser = useAuthenticatedUser();
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 transition hover:border-brand-500/50 dark:border-slate-800 dark:bg-slate-900">
      <button className="w-full text-left" onClick={() => setExpanded((value) => !value)} aria-expanded={expanded}>
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-300"><FileText className="h-4 w-4" /></div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-2"><p className="truncate text-sm font-bold text-slate-900 dark:text-white"><span className="mr-1.5 text-brand-500">{source.citationRank}.</span>{source.title}</p>{expanded ? <ChevronUp className="h-4 w-4 shrink-0 text-slate-400" /> : <ChevronDown className="h-4 w-4 shrink-0 text-slate-400" />}</div>
            <p className="mt-1 text-xs text-slate-500">{source.department}{source.page ? ` · Page ${source.page}` : ""}{source.section ? ` · ${source.section}` : ""}</p>
          </div>
        </div>
      </button>
      <div className="mt-3 flex items-center justify-between"><Badge tone="green">{Math.round((source.relevanceScore ?? 0) * 100)}% relevant</Badge>{currentUser.role === "admin" && <Badge tone="purple"><LockKeyhole className="mr-1 h-3 w-3" />{source.accessLevel}</Badge>}</div>
      {expanded && (
        <div className="mt-3 border-t border-slate-100 pt-3 dark:border-slate-800">
          <p className="text-xs leading-5 text-slate-600 dark:text-slate-300">“{source.snippet}”</p>
          <p className="mt-2 text-[10px] text-slate-400">{source.fileName}{source.version ? ` · version ${source.version}` : ""}{source.effectiveDate ? ` · effective ${source.effectiveDate}` : ""}</p>
        </div>
      )}
    </article>
  );
}
