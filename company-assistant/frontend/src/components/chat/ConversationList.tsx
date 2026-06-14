import { Clock3, MessageSquarePlus, Search, SlidersHorizontal } from "lucide-react";
import { useMemo, useState } from "react";
import { useChat } from "../../context/ChatContext";
import { Button } from "../common/Button";
import { SkeletonRows } from "../common/States";

export function ConversationList() {
  const { conversations, activeConversationId, isLoading, selectConversation, startNewChat } = useChat();
  const [query, setQuery] = useState("");
  const visible = useMemo(() => conversations.filter((item) => item.title.toLowerCase().includes(query.toLowerCase())), [conversations, query]);

  return (
    <section className="flex h-full w-[270px] shrink-0 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950" aria-label="Conversations">
      <div className="border-b border-slate-200 p-4 dark:border-slate-800"><Button className="w-full" onClick={startNewChat}><MessageSquarePlus className="h-4 w-4" />New conversation</Button><div className="relative mt-3"><label className="sr-only" htmlFor="conversation-search">Search conversations</label><Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" /><input id="conversation-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search history" className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pl-9 pr-9 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-50 dark:border-slate-700 dark:bg-slate-900 dark:text-white" /><SlidersHorizontal className="absolute right-3 top-2.5 h-4 w-4 text-slate-400" /></div></div>
      <div className="min-h-0 flex-1 overflow-y-auto p-3"><div className="mb-2 flex items-center justify-between px-2"><p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-400">Recent</p><Clock3 className="h-3.5 w-3.5 text-slate-400" /></div>{isLoading && conversations.length === 0 ? <SkeletonRows count={6} /> : <div className="space-y-1">{visible.map((conversation) => <button key={conversation.id} onClick={() => void selectConversation(conversation.id)} className={`w-full rounded-xl p-3 text-left transition ${activeConversationId === conversation.id ? "bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-indigo-200" : "text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-900"}`}><p className="truncate text-sm font-semibold">{conversation.title}</p><p className="mt-1 text-[11px] text-slate-400">{new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(conversation.updatedAt))}</p></button>)}{visible.length === 0 && <p className="px-3 py-8 text-center text-sm text-slate-400">No matching conversations.</p>}</div>}</div>
      <div className="border-t border-slate-200 p-4 text-center text-xs text-slate-400 dark:border-slate-800">Local MVP conversation history</div>
    </section>
  );
}
