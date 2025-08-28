import cv2


def _clip(x1, y1, x2, y2, w, h):
    x1 = max(0, min(int(x1), w - 1))
    y1 = max(0, min(int(y1), h - 1))
    x2 = max(0, min(int(x2), w - 1))
    y2 = max(0, min(int(y2), h - 1))
    if x2 < x1: x1, x2 = x2, x1
    if y2 < y1: y1, y2 = y2, y1
    return x1, y1, x2, y2

def _odd(k):
    k = max(5, int(k))
    return k if k % 2 == 1 else k + 1

def draw_redactions(img, boxes_xyxy, pad=6, blur_strength=35):
    if img is None or len(boxes_xyxy) == 0:
        return img.copy(), []

    h, w = img.shape[:2]
    out = img.copy()

    k = _odd(max(blur_strength, int(0.015 * max(w, h))))
    blurred = cv2.GaussianBlur(out, (k, k), 0)

    final_boxes = []
    for x1, y1, x2, y2 in boxes_xyxy:
        x1, y1, x2, y2 = x1 - pad, y1 - pad, x2 + pad, y2 + pad
        x1, y1, x2, y2 = _clip(x1, y1, x2, y2, w, h)
        if x2 <= x1 or y2 <= y1:
            continue
        out[y1:y2, x1:x2] = blurred[y1:y2, x1:x2]
        final_boxes.append([x1, y1, x2, y2])

    return out, final_boxes