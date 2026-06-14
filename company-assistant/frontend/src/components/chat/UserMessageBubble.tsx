import type { ChatMessage } from "../../types";

export function UserMessageBubble({ message }: { message: ChatMessage }) {
  return <article className="ml-auto max-w-[85%] rounded-2xl rounded-br-md bg-navy-950 px-4 py-3 text-sm leading-6 text-white shadow-sm"><p>{message.content}</p><p className="mt-1 text-right text-[10px] text-slate-400">{new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit" }).format(new Date(message.createdAt))}</p></article>;
}

