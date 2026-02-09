import { useCallback, useRef, useState } from "react";
import Modal from "../common/Modal";
import Spinner from "../common/Spinner";
import { uploadPdf } from "../../api/ingest";

interface UploadModalProps {
  open: boolean;
  onClose: () => void;
}

export default function UploadModal({ open, onClose }: UploadModalProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "indexing" | "done" | "error">("idle");
  const [result, setResult] = useState<string>("");

  const reset = () => {
    setProgress(null);
    setStatus("idle");
    setResult("");
  };

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setStatus("error");
      setResult("Only PDF files are supported.");
      return;
    }
    setStatus("uploading");
    setProgress(0);
    try {
      const resp = await uploadPdf(file, (pct) => {
        setProgress(pct);
        if (pct >= 100) setStatus("indexing");
      });
      setStatus("done");
      setResult(`Document #${resp.document_id} indexed successfully.`);
    } catch (err: unknown) {
      setStatus("error");
      const msg = err instanceof Error ? err.message : "Upload failed";
      setResult(msg);
    }
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Modal open={open} onClose={handleClose} title="Upload PDF">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => status === "idle" && inputRef.current?.click()}
        className={`
          flex flex-col items-center justify-center gap-3 p-8
          border-2 border-dashed rounded-xl transition-colors cursor-pointer
          ${dragging ? "border-accent bg-accent/5" : "border-theme hover:border-accent/50"}
        `}
      >
        {status === "idle" && (
          <>
            <svg className="w-10 h-10 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 16V4m0 0l-4 4m4-4l4 4M4 20h16" />
            </svg>
            <p className="text-sm text-secondary">
              Drag & drop a PDF here, or <span className="text-accent">click to browse</span>
            </p>
          </>
        )}

        {(status === "uploading" || status === "indexing") && (
          <>
            <Spinner size={32} />
            <p className="text-sm text-secondary">
              {status === "uploading"
                ? `Uploading... ${progress ?? 0}%`
                : "Indexing document (OCR + embeddings)..."}
            </p>
            {progress !== null && (
              <div className="w-full bg-surface-2 rounded-full h-1.5 mt-1">
                <div
                  className="bg-accent h-1.5 rounded-full transition-all"
                  style={{ width: `${Math.min(progress, 100)}%` }}
                />
              </div>
            )}
          </>
        )}

        {status === "done" && (
          <div className="text-center">
            <svg className="w-10 h-10 mx-auto text-green-500 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            <p className="text-sm text-primary">{result}</p>
            <button
              onClick={(e) => {
                e.stopPropagation();
                reset();
              }}
              className="mt-3 px-4 py-1.5 text-xs font-medium bg-accent text-white rounded-md hover:bg-[var(--color-accent-hover)] transition-colors cursor-pointer"
            >
              Upload Another
            </button>
          </div>
        )}

        {status === "error" && (
          <div className="text-center">
            <svg className="w-10 h-10 mx-auto text-red-500 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <p className="text-sm text-red-400">{result}</p>
            <button
              onClick={(e) => {
                e.stopPropagation();
                reset();
              }}
              className="mt-3 px-4 py-1.5 text-xs font-medium bg-surface-2 text-primary rounded-md hover:bg-surface transition-colors cursor-pointer"
            >
              Try Again
            </button>
          </div>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={onFileSelect}
      />
    </Modal>
  );
}
