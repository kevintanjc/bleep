import cv2
from ultralytics import YOLO

# Load the YOLOv8 model
model = YOLO("backend/LP-detection.pt")

# Load the input image
img1 = cv2.imread('backend/resources/images/img1.jpg')
img2 = cv2.imread('backend/resources/images/img2.jpeg')
images = [img1, img2]

# Run detection
for idx, img in enumerate([img1, img2], start=1):
    results = model(img)

    # Save results (YOLO saves predictions automatically if you call .save())
    results[0].save(filename=f"pred_{idx}.jpg")

    # If you want crops of detections:
    for j, box in enumerate(results[0].boxes.xyxy):
        x1, y1, x2, y2 = map(int, box)
        crop = img[y1:y2, x1:x2]
        cv2.imwrite(f"license_plate_{idx}_{j}.jpg", crop)