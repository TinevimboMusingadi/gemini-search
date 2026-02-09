import { useCallback, useEffect, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";
import { getPdfUrl, getPageRegions } from "../../api/documents";
import { useAppStore } from "../../store/appStore";
import type { RegionDetail } from "../../types/api";
import RegionOverlay from "./RegionOverlay";
import PageNav from "./PageNav";
import Spinner from "../common/Spinner";

// Configure pdf.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export default function PdfViewer() {
  const { activeDocumentId, activePageNum, setActivePage } = useAppStore();
  const [totalPages, setTotalPages] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [regions, setRegions] = useState<RegionDetail[]>([]);
  const [pageWidth, setPageWidth] = useState(0);
  const [pageHeight, setPageHeight] = useState(0);
  const [loading, setLoading] = useState(true);

  // Fetch regions when page changes
  useEffect(() => {
    if (!activeDocumentId) return;
    setRegions([]);
    getPageRegions(activeDocumentId, activePageNum)
      .then(setRegions)
      .catch(() => setRegions([]));
  }, [activeDocumentId, activePageNum]);

  const onDocumentLoadSuccess = useCallback(
    ({ numPages }: { numPages: number }) => {
      setTotalPages(numPages);
      setLoading(false);
    },
    []
  );

  const onPageLoadSuccess = useCallback(
    ({ width, height }: { width: number; height: number }) => {
      setPageWidth(width);
      setPageHeight(height);
    },
    []
  );

  if (!activeDocumentId) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-secondary">
        <svg className="w-16 h-16 mb-4 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-sm">Select a document to view</p>
      </div>
    );
  }

  // The scale factor for region overlays:
  // react-pdf renders at `width * zoom`. Region coords are in the original page pixel space.
  // We need: rendered_coord = original_coord * (rendered_width / original_width)
  const scale = pageWidth > 0 ? (pageWidth * zoom) / pageWidth : zoom;
  // Simplifies to just `zoom` if page is rendered at `width * zoom` and regions are in page coords.
  // But react-pdf renders at `scale` prop, so rendered = original * zoom.

  return (
    <div className="flex flex-col h-full">
      {/* PDF canvas area */}
      <div className="flex-1 overflow-auto flex justify-center p-4 bg-app">
        {loading && (
          <div className="flex items-center justify-center py-16">
            <Spinner size={32} />
          </div>
        )}
        <Document
          file={getPdfUrl(activeDocumentId)}
          onLoadSuccess={onDocumentLoadSuccess}
          loading=""
          className={loading ? "hidden" : ""}
        >
          <div className="relative inline-block shadow-xl">
            <Page
              pageNumber={activePageNum}
              scale={zoom}
              onLoadSuccess={onPageLoadSuccess}
              loading=""
              renderTextLayer={true}
              renderAnnotationLayer={true}
            />
            {/* Region overlays */}
            {pageWidth > 0 && pageHeight > 0 && (
              <div
                className="absolute top-0 left-0"
                style={{
                  width: pageWidth * zoom,
                  height: pageHeight * zoom,
                }}
              >
                <RegionOverlay regions={regions} scale={scale} />
              </div>
            )}
          </div>
        </Document>
      </div>

      {/* Page navigation bar */}
      {totalPages > 0 && (
        <PageNav
          currentPage={activePageNum}
          totalPages={totalPages}
          onPageChange={setActivePage}
          zoom={zoom}
          onZoomChange={setZoom}
        />
      )}
    </div>
  );
}
