import { ChevronDown, Library, PanelRightOpen, Plus } from "lucide-react";
import { useState } from "react";
import { ChatInput } from "../components/chat/ChatInput";
import { ChatThread } from "../components/chat/ChatThread";
import { ConversationList } from "../components/chat/ConversationList";
import { SourcePanel } from "../components/sources/SourcePanel";
import { useChat } from "../context/ChatContext";

export function ChatPage() {
  const { departmentFilter, setDepartmentFilter, startNewChat, latestSources } = useChat();
  const [sourceDrawerOpen, setSourceDrawerOpen] = useState(false);

  return (
    <div className="flex h-full min-h-[calc(100vh-4rem)] overflow-hidden">
      <div className="hidden lg:block"><ConversationList /></div>
      <section className="flex min-w-0 flex-1 flex-col bg-slate-50 dark:bg-slate-950">
        <div className="flex min-h-14 items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 dark:border-slate-800 dark:bg-slate-950">
          <div className="flex min-w-0 items-center gap-2">
            <div className="relative">
              <label htmlFor="department-filter" className="sr-only">Department filter</label>
              <select id="department-filter" value={departmentFilter} onChange={(event) => setDepartmentFilter(event.target.value)} className="appearance-none rounded-xl border border-slate-200 bg-white py-2 pl-3 pr-8 text-xs font-semibold text-slate-600 outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
                <option value="all">All departments</option>
                <option value="People">People</option>
                <option value="Security">Security</option>
                <option value="Operations">Operations</option>
                <option value="Finance">Finance</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            </div>
            <span className="hidden items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-bold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 sm:inline-flex"><Library className="h-3 w-3" />Permission-filtered sources</span>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => void startNewChat()} className="hidden items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:border-brand-500 hover:text-brand-600 dark:border-slate-700 dark:text-slate-300 sm:flex"><Plus className="h-4 w-4" />New chat</button>
            <button onClick={() => setSourceDrawerOpen(true)} className="relative rounded-xl border border-slate-200 p-2 text-slate-600 dark:border-slate-700 dark:text-slate-300 min-[1280px]:hidden" aria-label="Open evidence panel">
              <PanelRightOpen className="h-4 w-4" />
              {latestSources.length > 0 && <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand-500 px-1 text-[9px] font-bold text-white">{latestSources.length}</span>}
            </button>
          </div>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto"><ChatThread /></div>
        <ChatInput />
      </section>
      <div className="hidden min-[1280px]:block"><SourcePanel /></div>
      {sourceDrawerOpen && (
        <>
          <button className="fixed inset-0 z-40 bg-slate-950/40 min-[1280px]:hidden" onClick={() => setSourceDrawerOpen(false)} aria-label="Close evidence overlay" />
          <SourcePanel mobile onClose={() => setSourceDrawerOpen(false)} />
        </>
      )}
    </div>
  );
}
