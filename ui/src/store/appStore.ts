import { create } from "zustand";
import type {
  SearchResultItem,
  SearchMode,
  RegionDetail,
  MessageSchema,
} from "../types/api";

export type Theme = "dark" | "light";

interface AppState {
  // -- Theme --
  theme: Theme;
  toggleTheme: () => void;

  // -- Sidebar --
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;

  // -- Active document --
  activeDocumentId: number | null;
  activePageNum: number;
  setActiveDocument: (docId: number, page?: number) => void;
  setActivePage: (page: number) => void;

  // -- Selected region (for chat context) --
  selectedRegion: RegionDetail | null;
  setSelectedRegion: (region: RegionDetail | null) => void;

  // -- Search --
  searchQuery: string;
  searchMode: SearchMode;
  searchResults: SearchResultItem[];
  searchLoading: boolean;
  searchError: string | null;
  setSearchQuery: (q: string) => void;
  setSearchMode: (m: SearchMode) => void;
  setSearchResults: (r: SearchResultItem[]) => void;
  setSearchLoading: (l: boolean) => void;
  setSearchError: (e: string | null) => void;

  // -- Chat --
  chatSessionId: string | null;
  chatMessages: MessageSchema[];
  chatLoading: boolean;
  setChatSessionId: (id: string | null) => void;
  setChatMessages: (msgs: MessageSchema[]) => void;
  addChatMessage: (msg: MessageSchema) => void;
  setChatLoading: (l: boolean) => void;
}

/** Read persisted theme or default to dark */
function getInitialTheme(): Theme {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem("theme");
    if (stored === "light" || stored === "dark") return stored;
  }
  return "dark";
}

export const useAppStore = create<AppState>((set) => ({
  // -- Theme --
  theme: getInitialTheme(),
  toggleTheme: () =>
    set((s) => {
      const next = s.theme === "dark" ? "light" : "dark";
      localStorage.setItem("theme", next);
      document.documentElement.classList.toggle("dark", next === "dark");
      return { theme: next };
    }),

  // -- Sidebar --
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // -- Active document --
  activeDocumentId: null,
  activePageNum: 1,
  setActiveDocument: (docId, page = 1) =>
    set({ activeDocumentId: docId, activePageNum: page }),
  setActivePage: (page) => set({ activePageNum: page }),

  // -- Selected region --
  selectedRegion: null,
  setSelectedRegion: (region) => set({ selectedRegion: region }),

  // -- Search --
  searchQuery: "",
  searchMode: "hybrid",
  searchResults: [],
  searchLoading: false,
  searchError: null,
  setSearchQuery: (q) => set({ searchQuery: q }),
  setSearchMode: (m) => set({ searchMode: m }),
  setSearchResults: (r) => set({ searchResults: r, searchError: null }),
  setSearchLoading: (l) => set({ searchLoading: l }),
  setSearchError: (e) => set({ searchError: e }),

  // -- Chat --
  chatSessionId: null,
  chatMessages: [],
  chatLoading: false,
  setChatSessionId: (id) => set({ chatSessionId: id }),
  setChatMessages: (msgs) => set({ chatMessages: msgs }),
  addChatMessage: (msg) =>
    set((s) => ({ chatMessages: [...s.chatMessages, msg] })),
  setChatLoading: (l) => set({ chatLoading: l }),
}));
