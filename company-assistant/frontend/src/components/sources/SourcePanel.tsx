import { Info, Layers3, Library, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useAuthenticatedUser } from "../../context/AuthContext";
import { useChat } from "../../context/ChatContext";
import { EmptyState } from "../common/States";
import { SourceCard } from "./SourceCard";

type Tab = "sources" | "context" | "details";

export function SourcePanel({ mobile = false, onClose }: { mobile?: boolean; onClose?: () => void }) {
  const [tab, setTab] = useState<Tab>("sources");
  const { latestSources, activeConversation } = useChat();
  const currentUser = useAuthenticatedUser();
  const lastAssistant = useMemo(
    () => [...(activeConversation?.messages ?? [])].reverse().find((message) => message.role === "assistant"),
    [activeConversation],
  );
  const tabs: { id: Tab; label: string; icon: typeof Library }[] = [
    { id: "sources", label: "Sources", icon: Library },
    { id: "context", label: "Context", icon: Layers3 },
    { id: "details", label: "Details", icon: Info },
  ];

  const detailRows: [string, string | number][] = [
    ["Mode", lastAssistant?.metadata?.modelName === "mock-model" ? "Mock" : "Local RAG"],
    ["Model", lastAssistant?.metadata?.modelName ?? "Not available"],
    ["Embedding", lastAssistant?.metadata?.embeddingModel ?? "Not available"],
    ["Initial top-k", lastAssistant?.metadata?.retrievalTopK ?? "Not available"],
    ["Rerank top-n", lastAssistant?.metadata?.rerankTopN ?? "Not available"],
    ["Reranker", lastAssistant?.metadata?.reranker ?? "Not available"],
    ["Retrieval", lastAssistant?.metadata?.retrievalMs !== undefined ? `${lastAssistant.metadata.retrievalMs} ms` : "Not available"],
    ["Generation", lastAssistant?.metadata?.generationMs !== undefined ? `${lastAssistant.metadata.generationMs} ms` : "Not available"],
    ["Latency", lastAssistant?.metadata?.latencyMs !== undefined ? `${lastAssistant.metadata.latencyMs} ms` : "Not available"],
    ["Conversation", activeConversation?.id ?? "Not available"],
    ["Audit ID", lastAssistant?.metadata?.auditId ?? "Not available"],
  ];

  return (
    <aside className={`${mobile ? "fixed inset-y-0 right-0 z-50 shadow-2xl" : "h-full"} flex w-[340px] shrink-0 flex-col border-l border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-950`} aria-label="Answer evidence">
      <div className="flex h-14 items-center justify-between border-b border-slate-200 px-4 dark:border-slate-800">
        <div><p className="text-sm font-bold text-slate-950 dark:text-white">Answer evidence</p><p className="text-[10px] text-slate-400">Authorized citations and runtime metadata</p></div>
        {mobile && <button className="rounded-lg p-2 text-slate-500 hover:bg-slate-100" onClick={onClose} aria-label="Close evidence panel"><X className="h-5 w-5" /></button>}
      </div>
      <div className="grid grid-cols-3 border-b border-slate-200 bg-white p-1.5 dark:border-slate-800 dark:bg-slate-900" role="tablist">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)} className={`flex items-center justify-center gap-1.5 rounded-lg px-2 py-2 text-xs font-semibold transition ${tab === id ? "bg-brand-50 text-brand-600 dark:bg-brand-500/20 dark:text-indigo-200" : "text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800"}`}><Icon className="h-3.5 w-3.5" />{label}</button>
        ))}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-4" role="tabpanel">
        {tab === "sources" && (latestSources.length ? <div className="space-y-3">{latestSources.map((source) => <SourceCard key={source.id} source={source} />)}</div> : <EmptyState title="No sources yet" description="Authorized sources appear after a grounded answer." />)}
        {tab === "context" && (latestSources.length ? (
          <div className="space-y-3">
            {latestSources.map((source) => (
              <div key={source.id} className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                <p className="text-xs font-bold text-slate-900 dark:text-white">{source.section ?? source.title}</p>
                <p className="mt-2 text-xs leading-5 text-slate-600 dark:text-slate-300">{source.snippet}</p>
                {currentUser.role === "admin" && <p className="mt-3 border-t border-slate-100 pt-2 font-mono text-[10px] text-slate-400 dark:border-slate-800">chunk: {source.chunkId ?? "not provided"}</p>}
              </div>
            ))}
          </div>
        ) : <EmptyState title="No retrieved context" description="Ask a question to populate this tab." />)}
        {tab === "details" && (
          <dl className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 text-xs dark:border-slate-800 dark:bg-slate-900">
            {detailRows.map(([label, value]) => (
              <div key={label} className="flex items-start justify-between gap-3 border-b border-slate-100 pb-3 last:border-0 last:pb-0 dark:border-slate-800">
                <dt className="text-slate-400">{label}</dt><dd className="max-w-[175px] break-all text-right font-semibold text-slate-700 dark:text-slate-200">{value}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>
    </aside>
  );
}
