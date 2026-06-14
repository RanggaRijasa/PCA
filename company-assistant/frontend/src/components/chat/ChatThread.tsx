import { MessageSquareText } from "lucide-react";
import { useChat } from "../../context/ChatContext";
import { Button } from "../common/Button";
import { EmptyState, ErrorState, LoadingState } from "../common/States";
import { AssistantAnswerCard } from "./AssistantAnswerCard";
import { FollowUpSuggestions } from "./FollowUpSuggestions";
import { TypingIndicator } from "./TypingIndicator";
import { UserMessageBubble } from "./UserMessageBubble";

export function ChatThread() {
  const { activeConversation, isLoading, isStreaming, error, clearError, sendMessage } = useChat();
  if (isLoading && !activeConversation) return <LoadingState label="Loading conversation history..." />;
  if (error && !activeConversation) return <div className="p-5"><ErrorState message={error} onRetry={() => window.location.reload()} /></div>;
  if (!activeConversation || activeConversation.messages.length === 0) {
    return (
      <div className="p-6">
        <EmptyState
          title="Ask your first question"
          description="Answers use only permission-filtered, approved company documents and include citations."
          action={<Button onClick={() => void sendMessage("What is our remote work policy?")}><MessageSquareText className="h-4 w-4" />Try an example</Button>}
        />
      </div>
    );
  }

  const lastMessage = activeConversation.messages.at(-1);
  return (
    <div className="mx-auto w-full max-w-3xl space-y-4 px-5 py-6">
      {error && <ErrorState message={error} onRetry={clearError} />}
      {activeConversation.messages.map((message) => message.role === "user" ? <UserMessageBubble key={message.id} message={message} /> : <AssistantAnswerCard key={message.id} message={message} />)}
      {isStreaming && lastMessage?.role === "user" && <TypingIndicator />}
      {lastMessage?.role === "assistant" && lastMessage.status === "complete" && <FollowUpSuggestions onSelect={(value) => void sendMessage(value)} disabled={isStreaming} />}
    </div>
  );
}
