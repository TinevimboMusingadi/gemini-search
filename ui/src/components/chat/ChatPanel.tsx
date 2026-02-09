import { useCallback, useEffect, useRef } from "react";
import { useAppStore } from "../../store/appStore";
import {
  createSession,
  sendMessage,
  getSessionHistory,
} from "../../api/chat";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import Spinner from "../common/Spinner";

export default function ChatPanel() {
  const {
    chatSessionId,
    chatMessages,
    chatLoading,
    setChatSessionId,
    setChatMessages,
    addChatMessage,
    setChatLoading,
  } = useAppStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  // Initialize a session if we don't have one
  const ensureSession = useCallback(async () => {
    if (chatSessionId) return chatSessionId;
    const sess = await createSession();
    setChatSessionId(sess.session_id);
    return sess.session_id;
  }, [chatSessionId, setChatSessionId]);

  // Load history when session changes
  useEffect(() => {
    if (!chatSessionId) return;
    getSessionHistory(chatSessionId)
      .then((h) => setChatMessages(h.messages))
      .catch(() => {});
  }, [chatSessionId, setChatMessages]);

  const handleSend = useCallback(
    async (message: string, regionContext?: string) => {
      // Optimistic UI: add user message immediately
      const userMsg = {
        role: "user",
        content: regionContext ? `${message}\n\n${regionContext}` : message,
        timestamp: new Date().toISOString(),
      };
      addChatMessage(userMsg);
      setChatLoading(true);

      try {
        const sessionId = await ensureSession();
        const resp = await sendMessage(sessionId, message, regionContext);

        const modelMsg = {
          role: "model",
          content: resp.reply,
          timestamp: new Date().toISOString(),
        };
        addChatMessage(modelMsg);
      } catch {
        addChatMessage({
          role: "model",
          content: "Sorry, something went wrong. Please try again.",
          timestamp: new Date().toISOString(),
        });
      } finally {
        setChatLoading(false);
      }
    },
    [ensureSession, addChatMessage, setChatLoading]
  );

  const handleNewChat = useCallback(async () => {
    setChatMessages([]);
    setChatSessionId(null);
    const sess = await createSession();
    setChatSessionId(sess.session_id);
  }, [setChatMessages, setChatSessionId]);

  return (
    <div className="flex flex-col h-full bg-surface border-l border-theme">
      {/* Chat header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-theme">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <span className="text-xs font-semibold text-primary">Gemini Agent</span>
        </div>
        <button
          onClick={handleNewChat}
          className="px-2 py-1 text-[10px] font-medium text-secondary hover:text-primary
                     rounded-md hover:bg-surface-2 transition-colors cursor-pointer"
          title="New chat"
        >
          + New
        </button>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
        {chatMessages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-secondary">
            <svg className="w-10 h-10 mb-3 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-xs text-center">
              Ask questions about your PDFs.
              <br />
              Click a region on the page to add context.
            </p>
          </div>
        )}

        {chatMessages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {chatLoading && (
          <div className="flex items-center gap-2 py-2">
            <Spinner size={16} />
            <span className="text-xs text-secondary">Thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={chatLoading} />
    </div>
  );
}
