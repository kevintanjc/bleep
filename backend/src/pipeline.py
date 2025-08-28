from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import json
import os
import cv2

from src.lp_detector import load_lp_dectector, detect
from src.ocr import ocr_words, compile_patterns, detect_ids_in_words
from src.redactor import draw_redactions
from src.pii_analyser import build_analyzer

# Singletons
_SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_lg")
_ANALYZER = build_analyzer(spacy_model=_SPACY_MODEL, use_distilbert=True)

# Narrow this per use case if you want speed
_PII_ENTITIES = [
    "PERSON",
    "ORGANIZATION",
    "LOCATION",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "IBAN_CODE"
]

def _word_text(w: Dict[str, Any]) -> str:
    return (w.get("text") or w.get("word") or "").strip()

def _word_bbox(w: Dict[str, Any]) -> Tuple[int, int, int, int]:
    b = w.get("bbox") or w.get("box") or w.get("xyxy")
    if not b:
        return 0, 0, 0, 0
    x1, y1, x2, y2 = b
    return int(x1), int(y1), int(x2), int(y2)

def _index_ocr_words(words: List[Dict[str, Any]]) -> Tuple[str, List[Tuple[int, int, Tuple[int, int, int, int]]]]:
    # Reading order, then build a single text with char spans per word
    words_sorted = sorted(words, key=lambda w: (_word_bbox(w)[1], _word_bbox(w)[0]))
    parts: List[str] = []
    spans: List[Tuple[int, int, Tuple[int, int, int, int]]] = []
    cursor = 0
    for w in words_sorted:
        t = _word_text(w)
        if not t:
            continue
        if parts:
            parts.append(" ")
            cursor += 1
        start = cursor
        parts.append(t)
        cursor += len(t)
        spans.append((start, cursor, _word_bbox(w)))
    return "".join(parts), spans

def _union_boxes_for_span(spans: List[Tuple[int, int, Tuple[int, int, int, int]]], s: int, e: int) -> Optional[List[int]]:
    hit = [b for ws, we, b in spans if not (e <= ws or s >= we)]
    if not hit:
        return None
    x1 = min(b[0] for b in hit)
    y1 = min(b[1] for b in hit)
    x2 = max(b[2] for b in hit)
    y2 = max(b[3] for b in hit)
    return [x1, y1, x2, y2]

# ---------- Main pipeline ----------

def load_images_from_folder(folder: str) -> List[str]:
    p = Path(folder)
    return [str(f) for f in p.glob("*") if f.is_file()]

def run_pipeline(cfg: dict) -> List[str]:
    model_cfg = cfg["model"]
    io_cfg = cfg["io"]
    ocr_cfg = cfg["ocr"]

    model = load_lp_dectector(model_cfg["path"], model_cfg.get("conf_threshold", 0.25))
    patterns = compile_patterns(cfg["patterns"])

    input_dir = Path(io_cfg["input_dir"])
    out_dir_img = Path(io_cfg["results_img_dir"]); out_dir_img.mkdir(parents=True, exist_ok=True)
    out_dir_rpt = Path(io_cfg["results_rpt_dir"]); out_dir_rpt.mkdir(parents=True, exist_ok=True)

    reports: List[str] = []
    for idx, img_path in enumerate([p for p in input_dir.iterdir() if p.is_file()], start=1):
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        H, W = img.shape[:2]

        # detect license plates
        det = detect(model, img)
        det.save(filename=str(out_dir_img / f"pred_{idx}.jpg"))
        det_boxes = [[int(x1), int(y1), int(x2), int(y2)]
                     for x1, y1, x2, y2 in det.boxes.xyxy.detach().cpu().tolist()]

        # Persist crops only if needed for debugging or training
        if cfg.get("save_crops", False):
            for j, (x1, y1, x2, y2) in enumerate(det_boxes):
                crop = img[y1:y2, x1:x2]
                cv2.imwrite(str(out_dir_img / f"det_crop_{idx}_{j}.jpg"), crop)

        # B) OCR and regex PII
        words = ocr_words(img, ocr_cfg["config"], ocr_cfg["conf_threshold"])
        ocr_hits = detect_ids_in_words(words, patterns)
        ocr_boxes = [list(map(int, hit["bbox"])) for hit in ocr_hits if hit.get("bbox")]

        # C) Presidio + DistilBERT ONNX over OCR text
        text, spans = _index_ocr_words(words)
        pres_results = _ANALYZER.analyze(text=text, language="en", entities=cfg.get("pii_entities", _PII_ENTITIES))
        pres_boxes: List[List[int]] = []
        for r in pres_results:
            box = _union_boxes_for_span(spans, int(r.start), int(r.end))
            if box:
                pres_boxes.append(box)

        # redact after all boxes are drawn
        redact_boxes = det_boxes + ocr_boxes + pres_boxes
        redacted, final_boxes = draw_redactions(
            img,
            redact_boxes,
            pad=int(cfg.get("redact", {}).get("pad", 6)),
            blur_strength=int(cfg.get("redact", {}).get("blur_strength", 35)),
        )
        redacted_path = out_dir_img / f"redacted_{idx}.png"
        cv2.imwrite(str(redacted_path), redacted)

        # generate report
        presio_items = [{
            "entity_type": r.entity_type,
            "start": int(r.start),
            "end": int(r.end),
            "score": float(r.score),
            "text": text[int(r.start):int(r.end)],
        } for r in pres_results]

        report = {
            "source_image": str(img_path),
            "image_size_hw": [H, W],
            "detector_model": model_cfg["path"],
            "detections_xyxy": det_boxes,
            "ocr_findings": ocr_hits,
            "presidio_findings": presio_items,
            "redactions": {
                "count": len(final_boxes),
                "boxes_xyxy": final_boxes,
                "redacted_image_path": str(redacted_path),
            },
            "engines": {
                "detector": "YOLOv8",
                "ocr": "tesseract image_to_data",
                "nlp": "spaCy + Presidio + DistilBERT ONNX",
            },
        }
        rp = out_dir_rpt / f"report_{idx}.json"
        with open(rp, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        reports.append(str(rp))

    return reports
