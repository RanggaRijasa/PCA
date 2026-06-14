import { Bot, Check, Copy, Sparkles } from "lucide-react";
import { useState } from "react";
import type { ChatMessage } from "../../types";
import { FeedbackButtons } from "./FeedbackButtons";

export function AssistantAnswerCard({ message }: { message: ChatMessage }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  };

  const groundingLabel = message.metadata?.modelName === "mock-model" ? "Grounded mock" : "Grounded locally";

  return (
    <article
      className={`rounded-2xl border bg-white p-5 shadow-sm dark:bg-slate-900 ${message.status === "error" ? "border-red-200 dark:border-red-900" : "border-slate-200 dark:border-slate-800"}`}
      aria-live={message.status === "streaming" ? "polite" : "off"}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/20 dark:text-indigo-200">
          <Bot className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-sm font-bold text-slate-950 dark:text-white">Company Assistant</p>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
              <Sparkles className="h-3 w-3" />{groundingLabel}
            </span>
          </div>
          <p className="mt-0.5 text-xs text-slate-400">
            {new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit" }).format(new Date(message.createdAt))}
          </p>
        </div>
      </div>
      <div className="ml-0 mt-4 whitespace-pre-wrap text-[14px] leading-7 text-slate-700 dark:text-slate-200 sm:ml-12">
        {message.content}
        {message.status === "streaming" && <span className="ml-1 inline-block h-4 w-1.5 animate-pulse rounded-full bg-brand-500" />}
      </div>
      {message.status !== "streaming" && message.sources?.length === 0 && (
        <div className="ml-0 mt-4 rounded-xl bg-amber-50 p-3 text-xs text-amber-800 dark:bg-amber-950/30 dark:text-amber-200 sm:ml-12">
          No company source was found for this answer. Verify before using.
        </div>
      )}
      {message.status !== "streaming" && (
        <div className="ml-0 mt-4 flex items-center justify-between border-t border-slate-100 pt-3 dark:border-slate-800 sm:ml-12">
          <button className="inline-flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => void copy()}>
            {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
            {copied ? "Copied" : "Copy answer"}
          </button>
          <FeedbackButtons messageId={message.id} auditId={message.metadata?.auditId} />
        </div>
      )}
    </article>
  );
}
