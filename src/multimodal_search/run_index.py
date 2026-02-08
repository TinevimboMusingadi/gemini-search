"""
CLI entrypoint to index a PDF or a directory of PDFs.
Usage: python run_index.py <path_to_pdf_or_dir>
       run-index <path_to_pdf_or_dir>

Set LOG_LEVEL=DEBUG for per-step logs (OCR batches, regions, embeddings).
"""
import argparse
import logging
import os
import sys
from pathlib import Path

from multimodal_search.core.database import get_engine, init_db
from multimodal_search.indexer.pipeline import run_pipeline

_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
_level = getattr(logging, _LOG_LEVEL, logging.INFO)

logging.basicConfig(
    level=_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Index PDF(s) for multimodal search")
    parser.add_argument("path", type=str, help="Path to a PDF file or directory of PDFs")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.exists():
        logger.error("Path does not exist: %s", path)
        sys.exit(1)

    engine = get_engine()
    init_db(engine)

    if path.is_file():
        if path.suffix.lower() != ".pdf":
            logger.error("Not a PDF file: %s", path)
            sys.exit(1)
        run_pipeline(path)
        return

    pdfs = list(path.glob("**/*.pdf"))
    logger.info("Found %s PDF(s) under %s", len(pdfs), path)
    for p in pdfs:
        try:
            run_pipeline(p)
        except Exception as e:
            logger.exception("Failed to index %s: %s", p, e)
    logger.info("Done.")


if __name__ == "__main__":
    main()
