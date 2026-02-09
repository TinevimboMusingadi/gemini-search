import { useNavigate, useLocation } from "react-router-dom";
import ThemeToggle from "../common/ThemeToggle";
import { useAppStore } from "../../store/appStore";

interface HeaderProps {
  onUploadClick: () => void;
}

export default function Header({ onUploadClick }: HeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { sidebarOpen, setSidebarOpen, searchQuery } = useAppStore();

  const isSearch = location.pathname === "/" || location.pathname === "/search";
  const isHeroLanding = isSearch && !searchQuery;

  return (
    <header
      className={`h-11 flex items-center gap-3 px-4 shrink-0 transition-colors ${
        isHeroLanding
          ? "bg-app border-b border-transparent"
          : "bg-surface border-b border-theme"
      }`}
    >
      {/* Sidebar toggle (only in reader view) */}
      {!isSearch && (
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-2 transition-colors cursor-pointer"
          title="Toggle sidebar"
        >
          <svg className="w-5 h-5 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      )}

      {/* Logo / Brand */}
      <button
        onClick={() => navigate("/")}
        className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer"
      >
        <div className="w-6 h-6 rounded-md bg-accent/15 flex items-center justify-center">
          <svg className="w-3.5 h-3.5 text-accent" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v6h6v10H6z"/>
          </svg>
        </div>
        <span className="font-semibold text-sm text-primary tracking-tight">
          PDF Search
        </span>
      </button>

      {/* Nav tabs */}
      <nav className="flex items-center gap-0.5 ml-3">
        <button
          onClick={() => navigate("/")}
          className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors cursor-pointer ${
            isSearch
              ? "bg-surface-2 text-primary"
              : "text-secondary hover:text-primary hover:bg-surface-2"
          }`}
        >
          Search
        </button>
        <button
          onClick={() => navigate("/reader")}
          className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors cursor-pointer ${
            !isSearch
              ? "bg-surface-2 text-primary"
              : "text-secondary hover:text-primary hover:bg-surface-2"
          }`}
        >
          Reader
        </button>
      </nav>

      <div className="flex-1" />

      {/* Upload button */}
      <button
        onClick={onUploadClick}
        className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-medium
                   bg-accent/10 text-accent rounded-md hover:bg-accent/20
                   transition-colors cursor-pointer"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        Upload
      </button>

      {/* Theme toggle */}
      <ThemeToggle />
    </header>
  );
}
