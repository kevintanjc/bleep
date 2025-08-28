import cv2

def pad_and_clip(box, pad, width, height):
    x1, y1, x2, y2 = box
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(width - 1, x2 + pad)
    y2 = min(height - 1, y2 + pad)
    return [x1, y1, x2, y2]

def draw_redactions(image_bgr, boxes, pad=4):
    out = image_bgr.copy()
    h, w = out.shape[:2]
    final_boxes = []
    for b in boxes:
        x1, y1, x2, y2 = pad_and_clip(b, pad, w, h)
        final_boxes.append([x1, y1, x2, y2])
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 0, 0), thickness=-1)
    return out, final_boxes
