import { ChevronDown, Paperclip, Send } from "lucide-react";
import { useState } from "react";
import { useChat } from "../../context/ChatContext";

export function ChatInput() {
  const { sendMessage, isStreaming, sourceFilter, setSourceFilter } = useChat();
  const [value, setValue] = useState("");

  const submit = async () => {
    const message = value.trim();
    if (!message) return;
    setValue("");
    await sendMessage(message);
  };

  return (
    <div className="border-t border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
      <div className="rounded-2xl border border-slate-200 bg-white p-2 shadow-lg shadow-slate-200/50 transition focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-50 dark:border-slate-700 dark:bg-slate-900 dark:shadow-none">
        <label htmlFor="chat-message" className="sr-only">Ask a question about company documents</label>
        <textarea
          id="chat-message"
          rows={2}
          value={value}
          disabled={isStreaming}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void submit();
            }
          }}
          placeholder="Ask a question about company policies, procedures, documents..."
          className="max-h-36 min-h-14 w-full resize-none bg-transparent px-2 py-2 text-sm text-slate-800 outline-none placeholder:text-slate-400 dark:text-white"
        />
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1">
            <button disabled title="Attachments are disabled in the MVP" className="rounded-lg p-2 text-slate-300" aria-label="Attach file, disabled"><Paperclip className="h-4 w-4" /></button>
            <div className="relative">
              <label className="sr-only" htmlFor="input-source-scope">Source scope</label>
              <select id="input-source-scope" value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)} className="appearance-none rounded-lg bg-slate-50 py-2 pl-3 pr-8 text-xs font-semibold text-slate-600 outline-none dark:bg-slate-800 dark:text-slate-300">
                <option value="all">All approved sources</option>
                <option value="policies">Policies</option>
                <option value="handbooks">Handbooks</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-3.5 w-3.5 text-slate-400" />
            </div>
          </div>
          <button onClick={() => void submit()} disabled={!value.trim() || isStreaming} className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500 text-white transition hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-40" aria-label="Send message"><Send className="h-4 w-4" /></button>
        </div>
      </div>
      <p className="mt-2 text-center text-[10px] text-slate-400">Answers are local and source-grounded. Confirm important decisions with the document owner.</p>
    </div>
  );
}
