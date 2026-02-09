import { useState } from "react";

interface AiResponseProps {
  content: string;
  timestamp?: string;
  onNewResearch?: () => void;
}

/** Simple markdown-ish renderer: bold, headers, lists, paragraphs */
function renderMarkdown(text: string) {
  const lines = text.split("\n");
  const elements: JSX.Element[] = [];
  let listItems: string[] = [];
  let orderedItems: string[] = [];
  let key = 0;

  const flushUnordered = () => {
    if (listItems.length === 0) return;
    elements.push(
      <ul key={key++} className="list-disc list-inside space-y-1 my-2 text-primary/90">
        {listItems.map((li, i) => (
          <li key={i} className="text-[13.5px] leading-relaxed">
            {inlineFormat(li)}
          </li>
        ))}
      </ul>
    );
    listItems = [];
  };

  const flushOrdered = () => {
    if (orderedItems.length === 0) return;
    elements.push(
      <ol key={key++} className="list-decimal list-inside space-y-1.5 my-3 text-primary/90">
        {orderedItems.map((li, i) => (
          <li key={i} className="text-[13.5px] leading-relaxed">
            {inlineFormat(li)}
          </li>
        ))}
      </ol>
    );
    orderedItems = [];
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      flushUnordered();
      flushOrdered();
      continue;
    }

    // Headers
    if (trimmed.startsWith("### ")) {
      flushUnordered();
      flushOrdered();
      elements.push(
        <h4 key={key++} className="text-sm font-semibold text-primary mt-4 mb-1.5">
          {inlineFormat(trimmed.slice(4))}
        </h4>
      );
      continue;
    }
    if (trimmed.startsWith("## ")) {
      flushUnordered();
      flushOrdered();
      elements.push(
        <h3 key={key++} className="text-[15px] font-semibold text-primary mt-5 mb-2">
          {inlineFormat(trimmed.slice(3))}
        </h3>
      );
      continue;
    }
    if (trimmed.startsWith("# ")) {
      flushUnordered();
      flushOrdered();
      elements.push(
        <h2 key={key++} className="text-base font-bold text-primary mt-5 mb-2">
          {inlineFormat(trimmed.slice(2))}
        </h2>
      );
      continue;
    }

    // Ordered list: "1. ", "2. " etc.
    const olMatch = trimmed.match(/^(\d+)\.\s+(.+)$/);
    if (olMatch) {
      flushUnordered();
      orderedItems.push(olMatch[2]);
      continue;
    }

    // Unordered list
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      flushOrdered();
      listItems.push(trimmed.slice(2));
      continue;
    }

    // Regular paragraph
    flushUnordered();
    flushOrdered();
    elements.push(
      <p key={key++} className="text-[13.5px] leading-relaxed text-primary/90 my-1.5">
        {inlineFormat(trimmed)}
      </p>
    );
  }

  flushUnordered();
  flushOrdered();
  return elements;
}

/** Format inline bold (**text**) and inline code (`code`) */
function inlineFormat(text: string): (string | JSX.Element)[] {
  const parts: (string | JSX.Element)[] = [];
  // Match **bold**, *italic*, and `code`
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let idx = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    if (match[2]) {
      // Bold
      parts.push(
        <strong key={idx++} className="font-semibold text-primary">
          {match[2]}
        </strong>
      );
    } else if (match[3]) {
      // Italic
      parts.push(
        <em key={idx++} className="italic">
          {match[3]}
        </em>
      );
    } else if (match[4]) {
      // Code
      parts.push(
        <code
          key={idx++}
          className="px-1 py-0.5 text-[12px] bg-surface-2 rounded font-mono text-accent"
        >
          {match[4]}
        </code>
      );
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}

export default function AiResponse({
  content,
  timestamp,
  onNewResearch,
}: AiResponseProps) {
  const [liked, setLiked] = useState<"up" | "down" | null>(null);

  const timeStr = timestamp
    ? formatTimeAgo(new Date(timestamp))
    : "";

  return (
    <div className="group">
      {/* Time indicator */}
      {timeStr && (
        <div className="flex justify-end mb-3">
          <span className="text-[11px] text-secondary/50">{timeStr}</span>
        </div>
      )}

      {/* AI Response content — flowing document style */}
      <div className="prose-custom">{renderMarkdown(content)}</div>

      {/* Action buttons (like Google's share/like/dislike row) */}
      <div className="flex items-center gap-1 mt-4 pt-3 border-t border-theme/50">
        {/* Share */}
        <button
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-secondary
                     hover:bg-surface-2 transition-colors cursor-pointer"
          title="Share"
        >
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z"
            />
          </svg>
        </button>

        {/* Thumbs up */}
        <button
          onClick={() => setLiked(liked === "up" ? null : "up")}
          className={`flex items-center gap-1 px-2.5 py-1.5 rounded-full transition-colors cursor-pointer ${
            liked === "up"
              ? "bg-accent/15 text-accent"
              : "text-secondary hover:bg-surface-2"
          }`}
          title="Good response"
        >
          <svg
            className="w-3.5 h-3.5"
            fill={liked === "up" ? "currentColor" : "none"}
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6.633 10.5c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 012.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 00.322-1.672V3a.75.75 0 01.75-.75A2.25 2.25 0 0116.5 4.5c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 01-2.649 7.521c-.388.482-.987.729-1.605.729H14.23c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 00-1.423-.23H5.904M14.25 9h2.25M5.904 18.75c.083.205.173.405.27.602.197.4-.078.898-.523.898h-.908c-.889 0-1.713-.518-1.972-1.368a12 12 0 01-.521-3.507c0-1.553.295-3.036.831-4.398C3.387 10.203 4.167 9.75 5 9.75h1.053c.472 0 .745.556.5.96a8.958 8.958 0 00-1.302 4.665c0 1.194.232 2.333.654 3.375z"
            />
          </svg>
        </button>

        {/* Thumbs down */}
        <button
          onClick={() => setLiked(liked === "down" ? null : "down")}
          className={`flex items-center gap-1 px-2.5 py-1.5 rounded-full transition-colors cursor-pointer ${
            liked === "down"
              ? "bg-red-500/15 text-red-400"
              : "text-secondary hover:bg-surface-2"
          }`}
          title="Poor response"
        >
          <svg
            className="w-3.5 h-3.5"
            fill={liked === "down" ? "currentColor" : "none"}
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M7.5 15h2.25m8.024-9.75c.011.05.028.1.052.148.591 1.2.924 2.55.924 3.977a8.96 8.96 0 01-1.302 4.665c-.245.404.028.96.5.96h1.053c.832 0 1.612-.453 1.918-1.227.306-.774.511-1.598.637-2.447a11.97 11.97 0 00.194-2.121c0-.435-.023-.863-.068-1.285C20.321 6.944 19.402 6.25 18.375 6.25h-3.126c-.618 0-.991-.724-.725-1.282A4.488 4.488 0 0015.25 1.75.75.75 0 0014.5.999a4.498 4.498 0 00-.322 1.672c-.303.76-.93 1.331-1.653 1.715a9.04 9.04 0 00-2.86 2.4c-.5.634-1.226 1.08-2.032 1.08H5.904m8.346-1.116V4.5A2.25 2.25 0 0012 2.25M5.904 13.116c-.083-.205-.173-.405-.27-.602-.197-.4.078-.898.523-.898h.908c.889 0 1.713.518 1.972 1.368.339 1.11.521 2.287.521 3.507 0 1.553-.295 3.036-.831 4.398-.306.774-1.086 1.227-1.918 1.227H5.053c-.472 0-.745-.556-.5-.96a8.958 8.958 0 001.302-4.665 8.95 8.95 0 00-.654-3.375z"
            />
          </svg>
        </button>

        <div className="flex-1" />

        {/* New research */}
        {onNewResearch && (
          <button
            onClick={onNewResearch}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium
                       text-secondary hover:text-primary hover:bg-surface-2 transition-colors cursor-pointer"
          >
            <svg
              className="w-3.5 h-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182"
              />
            </svg>
            New research
          </button>
        )}
      </div>
    </div>
  );
}

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  return date.toLocaleDateString();
}
