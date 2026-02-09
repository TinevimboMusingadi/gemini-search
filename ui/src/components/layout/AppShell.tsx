import { useState, type ReactNode } from "react";
import Header from "./Header";
import UploadModal from "../ingest/UploadModal";

interface AppShellProps {
  children: ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <div className="flex flex-col h-full">
      <Header onUploadClick={() => setUploadOpen(true)} />
      <main className="flex-1 overflow-hidden">{children}</main>
      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </div>
  );
}
