import { useCallback, useEffect, useRef, useState } from "react";
import SearchBar from "../components/search/SearchBar";
import ResultsSidebar from "../components/search/ResultsSidebar";
import AiResponse from "../components/search/AiResponse";
import { useAppStore } from "../store/appStore";
import { createSession, sendMessage } from "../api/chat";
import { getDocuments } from "../api/documents";
import Spinner from "../components/common/Spinner";
import type { MessageSchema, DocumentListItem } from "../types/api";

export default function SearchPage() {
  const { searchResults, searchQuery, searchLoading, searchError } =
    useAppStore();

  // Agent conversation state
  const [agentSessionId, setAgentSessionId] = useState<string | null>(null);
  const [agentMessages, setAgentMessages] = useState<MessageSchema[]>([]);
  const [agentLoading, setAgentLoading] = useState(false);
  const contentEndRef = useRef<HTMLDivElement>(null);
  const prevQueryRef = useRef<string>("");

  // Auto-scroll on new messages
  useEffect(() => {
    contentEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [agentMessages]);

  // Ensure we have a session
  const ensureSession = useCallback(async () => {
    if (agentSessionId) return agentSessionId;
    const sess = await createSession();
    setAgentSessionId(sess.session_id);
    return sess.session_id;
  }, [agentSessionId]);

  // When search results arrive, auto-feed them to the agent for summarization
  useEffect(() => {
    if (
      searchResults.length === 0 ||
      searchLoading ||
      !searchQuery ||
      searchQuery === prevQueryRef.current
    ) {
      return;
    }
    prevQueryRef.current = searchQuery;

    const topResults = searchResults.slice(0, 8);
    const resultsContext = topResults
      .map(
        (r, i) =>
          `[${i + 1}] "${r.document_title}" p.${r.page_num} (${r.result_type}): ${r.snippet.slice(0, 200)}`
      )
      .join("\n");

    const agentPrompt = `The user searched for: "${searchQuery}"

Here are the top search results from the local PDF index:

${resultsContext}

Please provide a comprehensive summary of what these results tell us about "${searchQuery}". Highlight the key findings, mention which documents and pages are most relevant, and suggest follow-up questions the user might want to explore.`;

    (async () => {
      setAgentLoading(true);
      try {
        const sessionId = await ensureSession();
        const resp = await sendMessage(sessionId, agentPrompt);
        const modelMsg: MessageSchema = {
          role: "model",
          content: resp.reply,
          timestamp: new Date().toISOString(),
        };
        setAgentMessages((prev) => [...prev, modelMsg]);
      } catch {
        setAgentMessages((prev) => [
          ...prev,
          {
            role: "model",
            content:
              "I couldn't analyze these results right now. Browse the sources on the right to explore manually.",
            timestamp: new Date().toISOString(),
          },
        ]);
      } finally {
        setAgentLoading(false);
      }
    })();
  }, [searchResults, searchLoading, searchQuery, ensureSession]);

  // Handle follow-up messages from the user
  const handleFollowUp = useCallback(
    async (message: string) => {
      // Show user message as a follow-up query label
      const userMsg: MessageSchema = {
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
      };
      setAgentMessages((prev) => [...prev, userMsg]);
      setAgentLoading(true);
      try {
        const sessionId = await ensureSession();
        const resp = await sendMessage(sessionId, message);
        const modelMsg: MessageSchema = {
          role: "model",
          content: resp.reply,
          timestamp: new Date().toISOString(),
        };
        setAgentMessages((prev) => [...prev, modelMsg]);
      } catch {
        setAgentMessages((prev) => [
          ...prev,
          {
            role: "model",
            content: "Sorry, something went wrong. Please try again.",
            timestamp: new Date().toISOString(),
          },
        ]);
      } finally {
        setAgentLoading(false);
      }
    },
    [ensureSession]
  );

  // Start a fresh session
  const handleNewResearch = useCallback(async () => {
    setAgentMessages([]);
    setAgentSessionId(null);
    prevQueryRef.current = "";
    const sess = await createSession();
    setAgentSessionId(sess.session_id);
  }, []);

  const hasSearched = !!searchQuery;

  // Indexed documents for the landing ticker
  const [indexedDocs, setIndexedDocs] = useState<DocumentListItem[]>([]);
  useEffect(() => {
    getDocuments()
      .then(setIndexedDocs)
      .catch(() => {});
  }, []);

  // Follow-up input state
  const [followUpText, setFollowUpText] = useState("");

  const submitFollowUp = (e: React.FormEvent) => {
    e.preventDefault();
    const msg = followUpText.trim();
    if (!msg || agentLoading) return;
    handleFollowUp(msg);
    setFollowUpText("");
  };

  return (
    <div className="flex flex-col h-full">
      {/* ═══════════════════════════════════════════════════════
          HERO LANDING STATE — clean, monochrome
          ═══════════════════════════════════════════════════════ */}
      {!hasSearched && (
        <div className="flex-1 flex flex-col items-center justify-center px-6 pb-20">
          {/* Heading */}
          <h1 className="text-3xl md:text-4xl font-semibold text-primary mb-2 tracking-tight">
            Search your locally indexed documents
          </h1>
          <p className="text-sm text-secondary mb-10 max-w-lg text-center leading-relaxed">
            Multimodal search across text, images, tables, and diagrams.
            AI-powered analysis and summarization.
          </p>

          {/* Hero search bar */}
          <div className="w-full max-w-xl">
            <SearchBar variant="hero" />
          </div>

          {/* Indexed documents ticker */}
          {indexedDocs.length > 0 && (
            <div className="mt-14 w-full max-w-lg">
              <p className="text-[10px] uppercase tracking-widest text-secondary/40 text-center mb-3">
                {indexedDocs.length} indexed document{indexedDocs.length !== 1 ? "s" : ""}
              </p>
              <div className="relative overflow-hidden h-10">
                {/* Fade edges */}
                <div className="absolute left-0 top-0 bottom-0 w-12 bg-gradient-to-r from-[var(--color-bg)] to-transparent z-10" />
                <div className="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-[var(--color-bg)] to-transparent z-10" />
                {/* Scrolling track */}
                <div className="flex items-center gap-4 animate-scroll-left whitespace-nowrap">
                  {/* Double the items for seamless loop */}
                  {[...indexedDocs, ...indexedDocs].map((doc, i) => (
                    <div
                      key={`${doc.id}-${i}`}
                      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg
                                 bg-surface border border-theme shrink-0"
                    >
                      <div className="w-5 h-5 rounded bg-surface-2 flex items-center justify-center shrink-0">
                        <span className="text-[9px] font-bold text-secondary/70">
                          PDF
                        </span>
                      </div>
                      <span className="text-[11px] text-secondary/80 max-w-[200px] truncate">
                        {doc.filename}
                      </span>
                      <span className="text-[9px] text-secondary/40">
                        {doc.total_pages}p
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════
          RESULTS VIEW — Google AI Mode style
          ═══════════════════════════════════════════════════════ */}
      {hasSearched && (
        <>
          {/* Main content: AI response (left) + Sources (right) */}
          <div className="flex flex-1 min-h-0">
            {/* Left: AI research response — scrollable document flow */}
            <div className="flex-1 min-w-0 overflow-y-auto">
              <div className="max-w-2xl mx-auto px-6 py-6">
                {/* User query label */}
                <div className="flex items-start gap-2 mb-5">
                  <div className="w-7 h-7 rounded-full bg-accent/15 flex items-center justify-center shrink-0 mt-0.5">
                    <svg
                      className="w-3.5 h-3.5 text-accent"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-base font-medium text-primary">
                      {searchQuery}
                    </h2>
                  </div>
                </div>

                {/* Error state */}
                {searchError && (
                  <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl mb-4">
                    <p className="text-[13px] text-red-400">{searchError}</p>
                  </div>
                )}

                {/* Loading state — skeleton animation */}
                {(searchLoading || (agentLoading && agentMessages.filter(m => m.role === "model").length === 0)) && (
                  <div className="space-y-3 mb-6">
                    <div className="flex items-center gap-2 mb-4">
                      <Spinner size={16} />
                      <span className="text-[13px] text-secondary">
                        {searchLoading
                          ? "Searching your documents..."
                          : "Analyzing results..."}
                      </span>
                    </div>
                    {/* Skeleton lines */}
                    <div className="space-y-2.5 animate-pulse">
                      <div className="h-4 bg-surface-2 rounded-full w-3/4" />
                      <div className="h-4 bg-surface-2 rounded-full w-full" />
                      <div className="h-4 bg-surface-2 rounded-full w-5/6" />
                      <div className="h-4 bg-surface-2 rounded-full w-2/3" />
                      <div className="h-3 bg-surface-2 rounded-full w-0 mt-4" />
                      <div className="h-4 bg-surface-2 rounded-full w-full" />
                      <div className="h-4 bg-surface-2 rounded-full w-4/5" />
                    </div>
                  </div>
                )}

                {/* AI Responses — flowing document content */}
                {agentMessages.map((msg, i) =>
                  msg.role === "model" ? (
                    <div key={i} className="mb-6">
                      <AiResponse
                        content={msg.content}
                        timestamp={msg.timestamp}
                        onNewResearch={
                          i === agentMessages.length - 1 ||
                          (i === agentMessages.length - 2 && agentMessages[agentMessages.length - 1]?.role === "user")
                            ? handleNewResearch
                            : undefined
                        }
                      />
                    </div>
                  ) : (
                    /* Follow-up query label */
                    <div key={i} className="flex items-start gap-2 mb-5 mt-8 pt-6 border-t border-theme/50">
                      <div className="w-6 h-6 rounded-full bg-surface-2 flex items-center justify-center shrink-0 mt-0.5">
                        <svg
                          className="w-3 h-3 text-secondary"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
                          />
                        </svg>
                      </div>
                      <p className="text-[14px] font-medium text-primary">
                        {msg.content}
                      </p>
                    </div>
                  )
                )}

                {/* Loading indicator for follow-up */}
                {agentLoading && agentMessages.filter(m => m.role === "model").length > 0 && (
                  <div className="flex items-center gap-2 py-3">
                    <Spinner size={14} />
                    <span className="text-[12px] text-secondary">
                      Thinking...
                    </span>
                  </div>
                )}

                {/* ── Embedded follow-up input (Google "Ask anything" style) ── */}
                {!searchLoading && agentMessages.length > 0 && (
                  <form onSubmit={submitFollowUp} className="mt-6 mb-8">
                    <div
                      className="relative bg-surface border border-theme rounded-2xl
                                  transition-all focus-within:border-accent/40
                                  focus-within:shadow-sm focus-within:shadow-accent/5"
                    >
                      <input
                        type="text"
                        value={followUpText}
                        onChange={(e) => setFollowUpText(e.target.value)}
                        placeholder="Ask anything"
                        disabled={agentLoading}
                        className="w-full px-4 py-3 pr-12 text-[13.5px] bg-transparent text-primary
                                   placeholder:text-secondary/40 focus:outline-none rounded-2xl
                                   disabled:opacity-50"
                      />
                      {/* + button */}
                      <div className="absolute left-3 bottom-3 flex items-center gap-2 pointer-events-none opacity-0">
                        {/* hidden placeholder */}
                      </div>
                      <div className="absolute bottom-2 right-2 flex items-center gap-1.5">
                        <button
                          type="button"
                          className="w-7 h-7 flex items-center justify-center rounded-full
                                     hover:bg-surface-2 transition-colors cursor-pointer text-secondary"
                          title="Attach context"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                          </svg>
                        </button>
                        {followUpText.trim() && (
                          <button
                            type="submit"
                            disabled={agentLoading}
                            className="w-7 h-7 flex items-center justify-center rounded-full
                                       bg-accent text-white hover:bg-[var(--color-accent-hover)]
                                       transition-colors cursor-pointer disabled:opacity-40"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </div>
                  </form>
                )}

                <div ref={contentEndRef} />
              </div>
            </div>

            {/* Right: Sources sidebar */}
            <div className="border-l border-theme">
              <ResultsSidebar />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
