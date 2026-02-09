import { useNavigate } from "react-router-dom";
import type { SearchResultItem } from "../../types/api";
import { getCropUrl } from "../../api/documents";
import { useAppStore } from "../../store/appStore";

interface ResultCardProps {
  item: SearchResultItem;
  rank: number;
}

/** Color palette for source icons (deterministic based on doc id) */
const ICON_COLORS = [
  "bg-red-500/15 text-red-400",
  "bg-blue-500/15 text-blue-400",
  "bg-green-500/15 text-green-400",
  "bg-purple-500/15 text-purple-400",
  "bg-amber-500/15 text-amber-400",
  "bg-cyan-500/15 text-cyan-400",
  "bg-pink-500/15 text-pink-400",
  "bg-teal-500/15 text-teal-400",
];

export default function ResultCard({ item, rank }: ResultCardProps) {
  const navigate = useNavigate();
  const { setActiveDocument } = useAppStore();

  const handleClick = () => {
    setActiveDocument(item.document_id, item.page_num);
    navigate(`/reader/${item.document_id}`);
  };

  const colorClass = ICON_COLORS[item.document_id % ICON_COLORS.length];
  const initial = item.document_title.charAt(0).toUpperCase();
  const isImage = item.result_type === "image" && item.region_id;

  return (
    <button
      onClick={handleClick}
      className="w-full flex items-start gap-3 p-3 rounded-xl
                 bg-surface hover:bg-surface-2 border border-theme
                 hover:border-accent/30 transition-all cursor-pointer
                 text-left group"
    >
      {/* Source icon or thumbnail */}
      {isImage ? (
        <img
          src={getCropUrl(item.document_id, item.region_id!)}
          alt={item.snippet}
          className="w-10 h-10 object-cover rounded-lg border border-theme shrink-0"
          loading="lazy"
        />
      ) : (
        <div
          className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${colorClass}`}
        >
          <span className="text-sm font-semibold">{initial}</span>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 min-w-0">
        <h4 className="text-[12.5px] font-medium text-primary truncate group-hover:text-accent transition-colors">
          {item.document_title}
        </h4>
        <p className="text-[11px] text-secondary/70 line-clamp-2 mt-0.5 leading-relaxed">
          {item.snippet}
        </p>
        <div className="flex items-center gap-1.5 mt-1.5 text-[10px] text-secondary/50">
          <svg
            className="w-3 h-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
            />
          </svg>
          <span>Page {item.page_num}</span>
          <span className="opacity-40">·</span>
          <span className="capitalize">{item.result_type}</span>
          <span className="opacity-40">·</span>
          <span>#{rank}</span>
        </div>
      </div>
    </button>
  );
}
