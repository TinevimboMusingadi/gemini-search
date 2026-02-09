import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import { useAppStore } from "./store/appStore";
import AppShell from "./components/layout/AppShell";
import SearchPage from "./pages/SearchPage";
import ReaderPage from "./pages/ReaderPage";

export default function App() {
  const { theme } = useAppStore();

  // Sync theme class to <html> on mount
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/reader" element={<ReaderPage />} />
          <Route path="/reader/:documentId" element={<ReaderPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
