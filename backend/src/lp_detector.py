from ultralytics import YOLO

def load_lp_dectector(model_path: str, conf_threshold: float):
    model = YOLO(model_path)
    model.overrides["conf"] = conf_threshold
    return model

def detect(model, image_bgr):
    results = model(image_bgr)
    return results[0]
