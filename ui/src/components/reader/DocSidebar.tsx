import { useEffect, useState } from "react";
import { getDocuments, getDocument } from "../../api/documents";
import type { DocumentListItem, DocumentDetail } from "../../types/api";
import { useAppStore } from "../../store/appStore";
import Spinner from "../common/Spinner";

export default function DocSidebar() {
  const { activeDocumentId, activePageNum, setActiveDocument, setActivePage, sidebarOpen } =
    useAppStore();
  const [docs, setDocs] = useState<DocumentListItem[]>([]);
  const [expandedDoc, setExpandedDoc] = useState<number | null>(null);
  const [docDetail, setDocDetail] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch document list
  useEffect(() => {
    setLoading(true);
    getDocuments()
      .then(setDocs)
      .catch(() => setDocs([]))
      .finally(() => setLoading(false));
  }, []);

  // Fetch detail when expanding
  useEffect(() => {
    if (expandedDoc === null) {
      setDocDetail(null);
      return;
    }
    getDocument(expandedDoc)
      .then(setDocDetail)
      .catch(() => setDocDetail(null));
  }, [expandedDoc]);

  // Auto-expand active document
  useEffect(() => {
    if (activeDocumentId) setExpandedDoc(activeDocumentId);
  }, [activeDocumentId]);

  if (!sidebarOpen) return null;

  return (
    <div className="w-56 h-full bg-surface border-r border-theme flex flex-col shrink-0">
      {/* Header */}
      <div className="px-3 py-2 border-b border-theme">
        <span className="text-xs font-semibold text-secondary uppercase tracking-wider">
          Documents
        </span>
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto py-1">
        {loading && (
          <div className="flex justify-center py-8">
            <Spinner size={20} />
          </div>
        )}

        {!loading && docs.length === 0 && (
          <p className="px-3 py-4 text-xs text-secondary text-center">
            No documents indexed yet. Upload a PDF to get started.
          </p>
        )}

        {docs.map((doc) => {
          const isExpanded = expandedDoc === doc.id;
          const isActive = activeDocumentId === doc.id;

          return (
            <div key={doc.id}>
              {/* Document entry */}
              <button
                onClick={() => {
                  setExpandedDoc(isExpanded ? null : doc.id);
                  if (!isActive) {
                    setActiveDocument(doc.id, 1);
                  }
                }}
                className={`w-full flex items-center gap-2 px-3 py-1.5 text-left
                           transition-colors cursor-pointer ${
                             isActive
                               ? "bg-accent/10 text-accent"
                               : "text-primary hover:bg-surface-2"
                           }`}
              >
                {/* Expand chevron */}
                <svg
                  className={`w-3 h-3 text-secondary transition-transform shrink-0 ${
                    isExpanded ? "rotate-90" : ""
                  }`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>

                <svg className="w-3.5 h-3.5 text-secondary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>

                <span className="text-xs truncate">{doc.filename}</span>
                <span className="text-[10px] text-secondary ml-auto shrink-0">
                  {doc.total_pages}p
                </span>
              </button>

              {/* Page list */}
              {isExpanded && docDetail && docDetail.id === doc.id && (
                <div className="ml-5 border-l border-theme">
                  {docDetail.pages.map((page) => (
                    <button
                      key={page.id}
                      onClick={() => {
                        setActiveDocument(doc.id, page.page_num);
                        setActivePage(page.page_num);
                      }}
                      className={`w-full flex items-center gap-2 px-3 py-1 text-left
                                 transition-colors cursor-pointer ${
                                   isActive && activePageNum === page.page_num
                                     ? "text-accent bg-accent/5"
                                     : "text-secondary hover:text-primary hover:bg-surface-2"
                                 }`}
                    >
                      <span className="text-[11px]">Page {page.page_num}</span>
                      <div className="flex gap-1 ml-auto">
                        {page.has_ocr_text && (
                          <span className="w-1.5 h-1.5 rounded-full bg-green-500/60" title="Has OCR text" />
                        )}
                        {page.has_image && (
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-500/60" title="Has image" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
