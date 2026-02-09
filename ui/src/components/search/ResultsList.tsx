import { useAppStore } from "../../store/appStore";
import Spinner from "../common/Spinner";
import ResultCard from "./ResultCard";

export default function ResultsList() {
  const { searchResults, searchLoading, searchQuery } = useAppStore();

  if (searchLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size={32} />
      </div>
    );
  }

  if (!searchQuery) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-secondary">
        <svg className="w-16 h-16 mb-4 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35m0 0A7.5 7.5 0 104.5 4.5a7.5 7.5 0 0012.15 12.15z" />
        </svg>
        <p className="text-sm">Search across your indexed PDFs</p>
        <p className="text-xs mt-1 opacity-60">
          Try hybrid, keyword, or semantic search modes
        </p>
      </div>
    );
  }

  if (searchResults.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-secondary">
        <p className="text-sm">No results found for &ldquo;{searchQuery}&rdquo;</p>
        <p className="text-xs mt-1 opacity-60">
          Try different keywords or switch search mode
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
      {searchResults.map((item, i) => (
        <ResultCard key={`${item.document_id}-${item.page_id}-${item.chunk_id ?? item.region_id}-${i}`} item={item} rank={i + 1} />
      ))}
    </div>
  );
}
