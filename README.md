# Bleep

Bleep is a photo gallery that detects and redacts sensitive content in images. It combines object detection, OCR, and PII analysis to protect privacy in images storage.

Features:
- Imports or captures photos, then scans them for visual and textual PII.
- Detects license plates and other visual cues using a trained object detector.
- Extracts text with OCR and flags sensitive fields such as IDs, emails, phone numbers, and names.
- Redacts matches by blurring or boxing regions, then saves a redacted copy alongside the original.
- Original images will require a verification before they are accessible.

## This Project runs with [Expo SDK 51](https://expo.dev/go?sdkVersion=51&platform=android&device=true)

## Set Up (Local Machine)

Install [Tesseract OCR](https://github.com/tesseract-ocr/tessdoc) and confirm the binary is on PATH. Update config.yaml if you use a custom path.

Download [DistilBert](https://huggingface.co/Isotonic/distilbert_finetuned_ai4privacy_v2/blob/main/onnx/model.onnx) and place it in backend/resources/models

Inside bleep/backend, create an env file
```env
PYTESSERACT_PATH=<input file path>
ONNX_MODEL_PATH=backend/resources/models/model.onnx
TOKENIZER_PATH=backend/resources/models/tokenizer
NER_LABELS_PATH=backend/resources/models/labels.txt
```

Inside bleep/frontend, create an env file
```env
COMPUTER_LAN=http://<ip>
EMULATOR_LAN=http://10.x.x.2:<port>
BACKEND_URL=http://<ip>:<port>
```

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
## Side Note
Initial Set up may take a while install the necessary dependencies(~10mins)

