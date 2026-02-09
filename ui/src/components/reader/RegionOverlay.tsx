import type { RegionDetail } from "../../types/api";
import { useAppStore } from "../../store/appStore";

interface RegionOverlayProps {
  regions: RegionDetail[];
  /** Scale factor to map region pixel coords to the rendered canvas size */
  scale: number;
}

export default function RegionOverlay({ regions, scale }: RegionOverlayProps) {
  const { selectedRegion, setSelectedRegion } = useAppStore();

  return (
    <>
      {regions.map((r) => {
        const isSelected = selectedRegion?.id === r.id;
        const top = r.box_y0 * scale;
        const left = r.box_x0 * scale;
        const width = (r.box_x1 - r.box_x0) * scale;
        const height = (r.box_y1 - r.box_y0) * scale;

        return (
          <div
            key={r.id}
            onClick={(e) => {
              e.stopPropagation();
              setSelectedRegion(isSelected ? null : r);
            }}
            title={r.label}
            style={{ top, left, width, height }}
            className={`absolute cursor-pointer transition-all border-2 rounded-sm
              ${
                isSelected
                  ? "border-accent bg-accent/15 shadow-[0_0_8px_rgba(59,130,246,0.3)]"
                  : "border-transparent hover:border-accent/50 hover:bg-accent/5"
              }
            `}
          >
            {/* Label tooltip on hover */}
            <div className="absolute -top-7 left-0 hidden group-hover:block">
              <span className="px-2 py-1 text-[10px] bg-surface border border-theme rounded shadow text-primary whitespace-nowrap">
                {r.label}
              </span>
            </div>
          </div>
        );
      })}
    </>
  );
}
