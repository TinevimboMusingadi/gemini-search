import { useState } from "react";
import { useAppStore } from "../../store/appStore";
import Spinner from "../common/Spinner";
import ResultCard from "./ResultCard";

const COLLAPSED_COUNT = 5;

export default function ResultsSidebar() {
  const { searchResults, searchLoading, searchQuery, searchMode } =
    useAppStore();
  const [showAll, setShowAll] = useState(false);

  const displayResults = showAll
    ? searchResults
    : searchResults.slice(0, COLLAPSED_COUNT);
  const hasMore = searchResults.length > COLLAPSED_COUNT;

  return (
    <div className="w-80 xl:w-[360px] shrink-0 flex flex-col h-full">
      {/* Sources header */}
      <div className="flex items-center gap-2 px-4 pt-4 pb-2">
        <div className="flex items-center gap-2">
          {/* Stacked colored dots (like Google's source icons) */}
          <div className="flex -space-x-1.5">
            <div className="w-5 h-5 rounded-full bg-red-400/80 border-2 border-[var(--color-bg)] flex items-center justify-center">
              <span className="text-[8px] text-white font-bold">P</span>
            </div>
            <div className="w-5 h-5 rounded-full bg-blue-400/80 border-2 border-[var(--color-bg)] flex items-center justify-center">
              <span className="text-[8px] text-white font-bold">D</span>
            </div>
            <div className="w-5 h-5 rounded-full bg-green-400/80 border-2 border-[var(--color-bg)] flex items-center justify-center">
              <span className="text-[8px] text-white font-bold">F</span>
            </div>
          </div>
          <span className="text-[13px] font-semibold text-primary">
            {searchResults.length} source{searchResults.length !== 1 ? "s" : ""}
          </span>
        </div>

        <div className="flex-1" />

        <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface-2 text-secondary/60 uppercase tracking-wider">
          {searchMode}
        </span>
      </div>

      {/* Source cards */}
      <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-2">
        {searchLoading && (
          <div className="flex items-center justify-center py-12">
            <Spinner size={20} />
          </div>
        )}

        {!searchLoading && searchResults.length === 0 && searchQuery && (
          <div className="flex flex-col items-center justify-center py-12 text-secondary">
            <svg
              className="w-8 h-8 mb-2 opacity-30"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
              />
            </svg>
            <p className="text-xs">No sources found</p>
            <p className="text-[10px] mt-1 opacity-60">
              Try different keywords or modes
            </p>
          </div>
        )}

        {displayResults.map((item, i) => (
          <ResultCard
            key={`${item.document_id}-${item.page_id}-${item.chunk_id ?? item.region_id}-${i}`}
            item={item}
            rank={i + 1}
          />
        ))}

        {/* Show all / Show less */}
        {!searchLoading && hasMore && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="w-full py-2.5 text-[12px] font-medium text-accent
                       hover:bg-accent/5 rounded-xl transition-colors cursor-pointer
                       border border-theme hover:border-accent/30"
          >
            {showAll
              ? "Show less"
              : `Show all ${searchResults.length} sources`}
          </button>
        )}
      </div>
    </div>
  );
}
