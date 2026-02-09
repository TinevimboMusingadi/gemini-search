import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { useAppStore } from "../store/appStore";
import DocSidebar from "../components/reader/DocSidebar";
import PdfViewer from "../components/reader/PdfViewer";
import ChatPanel from "../components/chat/ChatPanel";

export default function ReaderPage() {
  const { documentId } = useParams<{ documentId?: string }>();
  const { activeDocumentId, setActiveDocument } = useAppStore();

  // Sync URL param to store
  useEffect(() => {
    if (documentId) {
      const id = parseInt(documentId, 10);
      if (!isNaN(id) && id !== activeDocumentId) {
        setActiveDocument(id, 1);
      }
    }
  }, [documentId, activeDocumentId, setActiveDocument]);

  return (
    <div className="flex h-full">
      {/* Left: Document sidebar */}
      <DocSidebar />

      {/* Center: PDF viewer */}
      <div className="flex-1 min-w-0">
        <PdfViewer />
      </div>

      {/* Right: Chat panel */}
      <div className="w-80 shrink-0">
        <ChatPanel />
      </div>
    </div>
  );
}
