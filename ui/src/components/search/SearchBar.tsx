import { useState } from "react";
import type { SearchMode } from "../../types/api";
import { useAppStore } from "../../store/appStore";
import { search as searchApi } from "../../api/search";

const MODES: { value: SearchMode; label: string }[] = [
  { value: "hybrid", label: "Hybrid" },
  { value: "keyword", label: "Keyword" },
  { value: "semantic", label: "Semantic" },
];

interface SearchBarProps {
  /** "hero" = large centered (landing), "compact" = slim top bar (results view) */
  variant?: "hero" | "compact";
  /** Called with the query string after a successful search trigger */
  onSearchTriggered?: (query: string) => void;
}

export default function SearchBar({
  variant = "compact",
  onSearchTriggered,
}: SearchBarProps) {
  const {
    searchQuery,
    searchMode,
    setSearchQuery,
    setSearchMode,
    setSearchResults,
    setSearchLoading,
    setSearchError,
  } = useAppStore();
  const [localQuery, setLocalQuery] = useState(searchQuery);

  const handleSearch = async (overrideQuery?: string) => {
    const q = (overrideQuery ?? localQuery).trim();
    if (!q) return;
    setLocalQuery(q);
    setSearchQuery(q);
    setSearchLoading(true);
    setSearchError(null);
    onSearchTriggered?.(q);
    try {
      const resp = await searchApi(q, searchMode);
      setSearchResults(resp.results);
    } catch (err: unknown) {
      setSearchResults([]);
      if (err instanceof Error) {
        setSearchError(err.message);
      } else {
        setSearchError(
          "Search request failed. Is the backend running on port 8000?"
        );
      }
      console.error("Search error:", err);
    } finally {
      setSearchLoading(false);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch();
  };

  /* ── Compact variant (top bar after results) ── */
  if (variant === "compact") {
    return (
      <form onSubmit={onSubmit} className="w-full max-w-2xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="flex-1 relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-4.35-4.35m0 0A7.5 7.5 0 104.5 4.5a7.5 7.5 0 0012.15 12.15z"
              />
            </svg>
            <input
              type="text"
              value={localQuery}
              onChange={(e) => setLocalQuery(e.target.value)}
              placeholder="Search your PDFs..."
              className="w-full pl-10 pr-4 py-2 text-sm bg-surface border border-theme
                         rounded-lg text-primary placeholder:text-secondary/50
                         focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/25
                         transition-colors"
            />
          </div>
          <div className="flex items-center bg-surface border border-theme rounded-lg overflow-hidden">
            {MODES.map((m) => (
              <button
                key={m.value}
                type="button"
                onClick={() => setSearchMode(m.value)}
                className={`px-2.5 py-2 text-[11px] font-medium transition-colors cursor-pointer ${
                  searchMode === m.value
                    ? "bg-accent text-white"
                    : "text-secondary hover:text-primary hover:bg-surface-2"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
          <button
            type="submit"
            className="px-3.5 py-2 text-sm font-medium bg-accent text-white rounded-lg
                       hover:bg-[var(--color-accent-hover)] transition-colors cursor-pointer"
          >
            Search
          </button>
        </div>
      </form>
    );
  }

  /* ── Hero variant (clean monochrome landing) ── */
  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={onSubmit}>
        {/* Main input box */}
        <div
          className="relative bg-surface border border-theme rounded-2xl
                      shadow-lg shadow-black/5 transition-all
                      focus-within:border-[var(--color-text-secondary)]/30 focus-within:shadow-black/10"
        >
          <input
            type="text"
            value={localQuery}
            onChange={(e) => setLocalQuery(e.target.value)}
            placeholder="Ask anything about your documents..."
            className="w-full px-5 pt-4 pb-10 text-base bg-transparent text-primary
                       placeholder:text-secondary/40
                       focus:outline-none rounded-2xl"
            autoFocus
          />
          {/* Bottom row: + icon, mode pills, submit */}
          <div className="absolute bottom-2.5 left-3 right-3 flex items-center">
            {/* Attach icon */}
            <button
              type="button"
              className="w-7 h-7 flex items-center justify-center rounded-full
                         hover:bg-surface-2 transition-colors cursor-pointer text-secondary/50"
              title="Attach context"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
            </button>

            <div className="flex-1" />

            {/* Mode pills — monochrome */}
            <div className="flex items-center gap-1 mr-2">
              {MODES.map((m) => (
                <button
                  key={m.value}
                  type="button"
                  onClick={() => setSearchMode(m.value)}
                  className={`px-2.5 py-1 text-[10px] font-medium rounded-full transition-colors cursor-pointer ${
                    searchMode === m.value
                      ? "bg-primary text-[var(--color-bg)]"
                      : "bg-surface-2 text-secondary hover:text-primary"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>

            {/* Submit arrow — monochrome */}
            <button
              type="submit"
              className="w-8 h-8 flex items-center justify-center rounded-full
                         bg-primary text-[var(--color-bg)] hover:opacity-80
                         transition-all cursor-pointer disabled:opacity-20"
              disabled={!localQuery.trim()}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </form>

      {/* Suggestion chips — monochrome */}
      <div className="flex flex-wrap items-center justify-center gap-2 mt-5">
        {[
          "What is this paper about?",
          "Summarize the key findings",
          "Find all figures and tables",
          "Explain the methodology",
        ].map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => {
              setLocalQuery(suggestion);
              handleSearch(suggestion);
            }}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs text-secondary/70
                       bg-surface border border-theme rounded-full
                       hover:border-[var(--color-text-secondary)]/30 hover:text-primary hover:bg-surface-2
                       transition-all cursor-pointer"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
