"""CLI to index PDF(s). Run from project root: python run_index.py <path_to_pdf_or_dir>."""
import sys
from pathlib import Path

# Add src to path so we can run without installing
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from multimodal_search.run_index import main

if __name__ == "__main__":
    main()
