from typing import List, Dict
import numpy as np
import pytesseract

from presidio_analyzer import AnalyzerEngine, RecognizerResult

_analyzer: AnalyzerEngine | None = None

def _get_analyzer(cfg) -> AnalyzerEngine:
    global _analyzer
    if _analyzer is not None:
        return _analyzer

    _analyzer = AnalyzerEngine()
    tesseract_cmd = cfg.get("ocr", {}).get("tesseract_cmd")
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    return _analyzer

def find_text_pii(img_rgb: np.ndarray, cfg) -> List[Dict]:
    """
    Returns word-level boxes that the analyzer flags as PII.
    Each box is a dict with x1 y1 x2 y2 label score
    """
    analyzer = _get_analyzer(cfg)

    # Word level OCR
    data = pytesseract.image_to_data(img_rgb, output_type=pytesseract.Output.DICT)
    n = len(data.get("text", []))
    out: List[Dict] = []
    h_img, w_img = img_rgb.shape[:2]

    # Analyze words individually with context off to keep it fast
    for i in range(n):
        txt = (data["text"][i] or "").strip()
        if not txt:
            continue

        # Simple heuristic, skip tiny boxes and junk
        conf = int(data.get("conf", ["-1"] * n)[i])
        if conf >= 0 and conf < int(cfg.get("ocr", {}).get("min_confidence", 50)):
            continue

        x = int(data["left"][i])
        y = int(data["top"][i])
        w = int(data["width"][i])
        h = int(data["height"][i])

        # Bounds clamp
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(w_img - 1, x + w)
        y2 = min(h_img - 1, y + h)

        # Run Presidio
        results: List[RecognizerResult] = analyzer.analyze(text=txt, language="en")
        if not results:
            continue

        # Take the highest score entity for this token
        best = max(results, key=lambda r: r.score)
        min_score = float(cfg.get("pii", {}).get("min_score", 0.6))
        if best.score < min_score:
            continue

        out.append({
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "label": best.entity_type,
            "score": float(best.score)
        })

    return out