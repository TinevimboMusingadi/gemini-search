import { useState } from "react";
import { useAppStore } from "../../store/appStore";

interface ChatInputProps {
  onSend: (message: string, regionContext?: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState("");
  const { selectedRegion, setSelectedRegion } = useAppStore();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const msg = text.trim();
    if (!msg || disabled) return;
    const regionCtx = selectedRegion
      ? `[Region: "${selectedRegion.label}" at (${selectedRegion.box_x0.toFixed(0)},${selectedRegion.box_y0.toFixed(0)})-(${selectedRegion.box_x1.toFixed(0)},${selectedRegion.box_y1.toFixed(0)})]`
      : undefined;
    onSend(msg, regionCtx);
    setText("");
    setSelectedRegion(null);
  };

  return (
    <form onSubmit={handleSubmit} className="p-3 border-t border-theme">
      {/* Region context chip */}
      {selectedRegion && (
        <div className="flex items-center gap-2 mb-2 px-2 py-1.5 bg-accent/10 border border-accent/30 rounded-lg">
          <svg className="w-3.5 h-3.5 text-accent shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.172 13.828a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.102 1.101" />
          </svg>
          <span className="text-[11px] text-accent truncate flex-1">
            {selectedRegion.label}
          </span>
          <button
            type="button"
            onClick={() => setSelectedRegion(null)}
            className="w-4 h-4 flex items-center justify-center rounded hover:bg-accent/20 cursor-pointer"
          >
            <svg className="w-3 h-3 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <div className="flex items-end gap-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          placeholder="Ask about your documents..."
          rows={1}
          className="flex-1 px-3 py-2 text-sm bg-surface-2 border border-theme rounded-lg
                     text-primary placeholder:text-secondary/50
                     focus:outline-none focus:border-accent/50 resize-none
                     min-h-[36px] max-h-[120px]"
          style={{ height: "36px" }}
          disabled={disabled}
        />
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="w-9 h-9 flex items-center justify-center rounded-lg bg-accent text-white
                     hover:bg-[var(--color-accent-hover)] disabled:opacity-40 disabled:cursor-not-allowed
                     transition-colors cursor-pointer shrink-0"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </form>
  );
}
