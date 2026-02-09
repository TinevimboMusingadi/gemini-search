import type { MessageSchema } from "../../types/api";

interface MessageBubbleProps {
  message: MessageSchema;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] px-3 py-2 rounded-xl text-sm leading-relaxed ${
          isUser
            ? "bg-accent text-white rounded-br-sm"
            : "bg-surface-2 text-primary rounded-bl-sm"
        }`}
      >
        {/* Render message content with basic whitespace preservation */}
        <div className="whitespace-pre-wrap break-words">{message.content}</div>
        <div
          className={`text-[10px] mt-1 ${
            isUser ? "text-white/60" : "text-secondary"
          }`}
        >
          {message.timestamp
            ? new Date(message.timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })
            : ""}
        </div>
      </div>
    </div>
  );
}
