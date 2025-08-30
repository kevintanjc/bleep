# Bleep

Bleep is a photo gallery that detects and redacts sensitive content in images. It combines object detection, OCR, and PII analysis to protect privacy in images storage.

Features:
- Imports or captures photos, then scans them for visual and textual PII.
- Detects license plates and other visual cues using a trained object detector.
- Extracts text with OCR and flags sensitive fields such as IDs, emails, phone numbers, and names.
- Redacts matches by blurring or boxing regions, then saves a redacted copy alongside the original.
- Original images will require a verification before they are accessible.


## Quick start

Install [Tesseract OCR](https://github.com/tesseract-ocr/tessdoc) and confirm the binary is on PATH. Update config.yaml if you use a custom path.

### macOS and Linux
```bash
git clone https://github.com/kevintanjc/bleep.git
cd bleep
chmod +x run.sh

./run.sh
```

### Windows
```bash
git clone https://github.com/kevintanjc/bleep.git
cd bleep

./run.bat
```
