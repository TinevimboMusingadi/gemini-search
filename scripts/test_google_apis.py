"""
Ping all Google APIs used by the indexer: Vision (OCR), Gemini (detection), Vertex (embeddings).
Run from project root: python scripts/test_google_apis.py
Uses .env (GOOGLE_API_KEY or GOOGLE_APPLICATION_CREDENTIALS, GEMINI_API_KEY, GCP_*).
"""
import sys
from pathlib import Path

# Project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

def main() -> None:
    from multimodal_search.core.config import get_settings

    settings = get_settings()
    results = []

    # 1. GCP Vision (OCR)
    try:
        from multimodal_search.services.gcp_vision import get_vision_client, batch_ocr

        client = get_vision_client()
        # Small valid image (Vision DOCUMENT_TEXT_DETECTION can reject 1x1)
        import io
        from PIL import Image
        img = Image.new("RGB", (64, 64), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        out = batch_ocr(client, [buf.getvalue()])
        if out and out[0][2] is None:
            results.append(("GCP Vision (OCR)", True, "OK"))
        else:
            err = out[0][2] if out else "no response"
            results.append(("GCP Vision (OCR)", False, str(err)))
    except Exception as e:
        results.append(("GCP Vision (OCR)", False, str(e)))

    # 2. Gemini (detection / chat)
    try:
        from multimodal_search.services.gemini_client import get_gemini_client

        client = get_gemini_client()
        r = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Reply with exactly: OK",
        )
        if r and r.text and "OK" in (r.text or "").upper():
            results.append(("Gemini", True, "OK"))
        else:
            results.append(("Gemini", False, (r.text or "empty")[:200]))
    except Exception as e:
        results.append(("Gemini", False, str(e)))

    # 3. Vertex AI (embeddings)
    try:
        from multimodal_search.services.vertex_embedder import embed_text

        dim = settings.embedding_dimension
        vecs = embed_text(["test"])
        if vecs and len(vecs) == 1 and len(vecs[0]) == dim:
            results.append(("Vertex AI (embeddings)", True, "OK"))
        else:
            results.append(("Vertex AI (embeddings)", False, "unexpected response"))
    except Exception as e:
        results.append(("Vertex AI (embeddings)", False, str(e)))

    # Print summary
    print("Google API connectivity:")
    print("-" * 60)
    for name, ok, msg in results:
        status = "PASS" if ok else "FAIL"
        print(f"  {name}: {status}  {msg}")
    print("-" * 60)
    all_ok = all(r[1] for r in results)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
