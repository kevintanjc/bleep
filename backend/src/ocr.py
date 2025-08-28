import pytesseract
import re

def ocr_words(image_bgr, psm_config: str, conf_threshold: int):
    data = pytesseract.image_to_data(
        image_bgr,
        output_type=pytesseract.Output.DICT,
        config=psm_config
    )
    words = []
    n = len(data["text"])
    for i in range(n):
        text = (data["text"][i] or "").strip()
        conf_raw = data["conf"][i]
        conf = int(conf_raw) if str(conf_raw).isdigit() else -1
        if text and conf >= conf_threshold:
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            words.append({
                "text": text,
                "conf": conf,
                "bbox": [int(x), int(y), int(x + w), int(y + h)]
            })
    return words

def compile_patterns(patterns_dict):
    return {name: re.compile(rx, re.IGNORECASE) for name, rx in patterns_dict.items()}

def detect_ids_in_words(words, compiled_patterns):
    findings = []
    for idx, w in enumerate(words):
        token = w["text"]
        for label, rx in compiled_patterns.items():
            if rx.search(token):
                findings.append({
                    "label": label,
                    "text": token,
                    "bbox": w["bbox"],
                    "word_index": idx,
                    "confidence": w["conf"],
                })
    return findings
