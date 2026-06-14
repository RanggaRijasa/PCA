import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { createConversation, getConversation, listConversations, sendMockChat, streamRealChat } from "../services/chatApi";
import { useLocalMocks } from "../services/apiClient";
import type { ChatMessage, Conversation, ConversationSummary, SourceCitation } from "../types";

type ChatContextValue = {
  conversations: ConversationSummary[];
  activeConversation: Conversation | null;
  activeConversationId: string | null;
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  departmentFilter: string;
  sourceFilter: string;
  latestSources: SourceCitation[];
  setDepartmentFilter: (value: string) => void;
  setSourceFilter: (value: string) => void;
  clearError: () => void;
  selectConversation: (id: string) => Promise<void>;
  startNewChat: () => Promise<void>;
  sendMessage: (message: string) => Promise<void>;
};

const ChatContext = createContext<ChatContextValue | undefined>(undefined);

const pause = (milliseconds: number) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));

export function ChatProvider({ children }: { children: ReactNode }) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [departmentFilter, setDepartmentFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");

  const selectConversation = useCallback(async (id: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const detail = await getConversation(id);
      setActiveConversation(detail);
      setActiveConversationId(id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load this conversation.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    listConversations()
      .then(async (items) => {
        setConversations(items);
        if (items[0]) await selectConversation(items[0].id);
        else setIsLoading(false);
      })
      .catch((caught: Error) => {
        setError(caught.message);
        setIsLoading(false);
      });
  }, [selectConversation]);

  const startNewChat = async () => {
    setError(null);
    try {
      const summary = await createConversation();
      setConversations((items) => [summary, ...items]);
      setActiveConversation({ ...summary, messages: [] });
      setActiveConversationId(summary.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create a new conversation.");
    }
  };

  const sendMessage = async (message: string) => {
    const cleanMessage = message.trim();
    if (!cleanMessage || isStreaming) return;

    let target = activeConversation;
    if (!target) {
      const summary = await createConversation();
      target = { ...summary, messages: [] };
      setConversations((items) => [summary, ...items]);
      setActiveConversationId(summary.id);
    }

    const timestamp = new Date().toISOString();
    const userMessage: ChatMessage = { id: `local_${crypto.randomUUID()}`, role: "user", content: cleanMessage, createdAt: timestamp, status: "complete" };
    const targetId = target.id;
    setActiveConversation({ ...target, messages: [...target.messages, userMessage] });
    setIsStreaming(true);
    setError(null);
    let streamingMessageId: string | null = null;

    try {
      if (useLocalMocks) {
        const response = await sendMockChat({ conversationId: targetId, message: cleanMessage, departmentFilter, sourceFilter });
        streamingMessageId = response.messageId;
        const assistantMessage: ChatMessage = { id: response.messageId, role: "assistant", content: "", createdAt: new Date().toISOString(), status: "streaming", sources: response.sources, metadata: response.metadata };
        setActiveConversation((current) => current ? { ...current, messages: [...current.messages, assistantMessage] } : current);

        const pieces = response.answer.match(/\S+\s*/g) ?? [response.answer];
        let streamed = "";
        for (const piece of pieces) {
          streamed += piece;
          setActiveConversation((current) => current ? {
            ...current,
            messages: current.messages.map((item) => item.id === response.messageId ? { ...item, content: streamed } : item),
          } : current);
          await pause(14);
        }
        setActiveConversation((current) => current ? {
          ...current,
          messages: current.messages.map((item) => item.id === response.messageId ? { ...item, status: "complete" } : item),
        } : current);
      } else {
        await streamRealChat(
          { conversationId: targetId, message: cleanMessage, departmentFilter, sourceFilter },
          (event) => {
            if (event.type === "start") {
              streamingMessageId = event.messageId;
              const assistantMessage: ChatMessage = { id: event.messageId, role: "assistant", content: "", createdAt: new Date().toISOString(), status: "streaming", sources: [] };
              setActiveConversation((current) => current ? { ...current, messages: [...current.messages, assistantMessage] } : current);
            } else if (event.type === "token") {
              const messageId = streamingMessageId;
              if (!messageId) return;
              setActiveConversation((current) => current ? {
                ...current,
                messages: current.messages.map((item) => item.id === messageId ? { ...item, content: item.content + event.content } : item),
              } : current);
            } else if (event.type === "final") {
              setActiveConversation((current) => current ? {
                ...current,
                messages: current.messages.map((item) => item.id === event.messageId ? {
                  ...item,
                  content: event.answer,
                  sources: event.sources,
                  metadata: event.metadata,
                  status: event.status,
                } : item),
              } : current);
            }
          },
        );
      }

      setActiveConversation((current) => current ? {
        ...current,
        title: current.title === "New chat" ? cleanMessage.slice(0, 48) : current.title,
      } : current);
      setConversations((items) => items.map((item) => item.id === targetId ? { ...item, title: item.title === "New chat" ? cleanMessage.slice(0, 48) : item.title, updatedAt: timestamp } : item));
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "The local RAG answer could not be loaded.";
      setError(message);
      setActiveConversation((current) => current ? {
        ...current,
        messages: streamingMessageId
          ? current.messages.map((item) => item.id === streamingMessageId ? { ...item, content: message, status: "error" } : item)
          : [...current.messages, { id: `error_${crypto.randomUUID()}`, role: "assistant", content: message, createdAt: new Date().toISOString(), status: "error" }],
      } : current);
    } finally {
      setIsStreaming(false);
    }
  };

  const latestSources = useMemo(() => {
    const assistantMessage = [...(activeConversation?.messages ?? [])].reverse().find((message) => message.role === "assistant" && message.sources?.length);
    return assistantMessage?.sources ?? [];
  }, [activeConversation]);

  return (
    <ChatContext.Provider value={{ conversations, activeConversation, activeConversationId, isLoading, isStreaming, error, departmentFilter, sourceFilter, latestSources, setDepartmentFilter, setSourceFilter, clearError: () => setError(null), selectConversation, startNewChat, sendMessage }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) throw new Error("useChat must be used within ChatProvider");
  return context;
}
