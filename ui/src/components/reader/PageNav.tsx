interface PageNavProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  zoom: number;
  onZoomChange: (zoom: number) => void;
}

export default function PageNav({
  currentPage,
  totalPages,
  onPageChange,
  zoom,
  onZoomChange,
}: PageNavProps) {
  return (
    <div className="flex items-center justify-center gap-3 py-2 px-4 bg-surface border-t border-theme">
      {/* Page navigation */}
      <button
        onClick={() => onPageChange(Math.max(1, currentPage - 1))}
        disabled={currentPage <= 1}
        className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-surface-2
                   disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
      >
        <svg className="w-4 h-4 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <span className="text-xs text-secondary font-mono min-w-[80px] text-center">
        {currentPage} / {totalPages}
      </span>

      <button
        onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
        disabled={currentPage >= totalPages}
        className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-surface-2
                   disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
      >
        <svg className="w-4 h-4 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </button>

      <div className="w-px h-5 bg-[var(--color-border)] mx-1" />

      {/* Zoom controls */}
      <button
        onClick={() => onZoomChange(Math.max(0.5, zoom - 0.1))}
        className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-surface-2 transition-colors cursor-pointer"
      >
        <svg className="w-4 h-4 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
        </svg>
      </button>

      <span className="text-xs text-secondary font-mono min-w-[45px] text-center">
        {Math.round(zoom * 100)}%
      </span>

      <button
        onClick={() => onZoomChange(Math.min(3, zoom + 0.1))}
        className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-surface-2 transition-colors cursor-pointer"
      >
        <svg className="w-4 h-4 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
        </svg>
      </button>

      <button
        onClick={() => onZoomChange(1)}
        className="px-2 py-1 text-[10px] text-secondary hover:text-primary font-medium
                   rounded-md hover:bg-surface-2 transition-colors cursor-pointer"
      >
        Reset
      </button>
    </div>
  );
}
