import { ThumbsDown, ThumbsUp } from "lucide-react";
import { useState } from "react";
import { submitFeedback } from "../../services/chatApi";
import { useToast } from "../../context/ToastContext";

export function FeedbackButtons({ messageId, auditId }: { messageId: string; auditId?: string }) {
  const [rating, setRating] = useState<"up" | "down" | null>(null);
  const { showToast } = useToast();

  const send = async (value: "up" | "down") => {
    try {
      await submitFeedback(messageId, value, auditId);
      setRating(value);
      showToast("Feedback recorded.");
    } catch (caught) {
      showToast(caught instanceof Error ? caught.message : "Feedback could not be sent.");
    }
  };

  return <div className="flex items-center gap-1" aria-label="Answer feedback"><button className={`rounded-lg p-2 transition hover:bg-slate-100 dark:hover:bg-slate-800 ${rating === "up" ? "text-emerald-600" : "text-slate-400"}`} onClick={() => void send("up")} aria-label="Helpful answer"><ThumbsUp className="h-4 w-4" /></button><button className={`rounded-lg p-2 transition hover:bg-slate-100 dark:hover:bg-slate-800 ${rating === "down" ? "text-red-600" : "text-slate-400"}`} onClick={() => void send("down")} aria-label="Unhelpful answer"><ThumbsDown className="h-4 w-4" /></button></div>;
}
