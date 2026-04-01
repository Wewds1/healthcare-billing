# OCR Pipeline Documentation

## Overview

The OCR feature processes an uploaded image or PDF in three stages:
1. Preprocessing with OpenCV for OCR readiness.
2. Text extraction with Tesseract.
3. Field parsing into structured healthcare billing data.

## Implemented Files

- `ocr/preprocessor.py`: document loading, deskewing, denoising, adaptive thresholding, ROI detection.
- `ocr/extractor.py`: document-type OCR configs and confidence scoring.
- `ocr/parser.py`: regex-based field extraction and field confidence hints.
- `ocr/pipeline.py`: orchestration and output payload assembly.
- `app/routers/ocr.py`: upload endpoints.

## API Endpoints

### POST /ocr/upload

Accepts multipart form data:
- `document_type`: one of `insurance_claim`, `invoice`, `patient_id`, `handwritten`
- `file`: image or PDF

Returns:
- extracted fields
- confidence scores
- raw OCR text
- OCR segment list with ROI boxes
- base64 preprocessed image

### POST /ocr/upload-and-create

Accepts multipart form data:
- `document_type`
- `patient_id`
- `procedure_id`
- `status` (optional, default `pending`)
- `diagnosis_code` (optional)
- `file`

Behavior:
- Runs OCR pipeline
- Extracts amount from OCR output when available
- Creates a billing record
- Returns both OCR output and created billing record id

## Sample PDF Generation

A generator script is available at `ocr/sample_docs/generate_sample_docs.py`.

It creates PDF samples in these folders:
- `ocr/sample_docs/insurance_claim`
- `ocr/sample_docs/invoice`
- `ocr/sample_docs/patient_id`
- `ocr/sample_docs/handwritten`

Each folder gets three variants:
- clear
- skewed
- low quality

Run:

```powershell
python ocr/sample_docs/generate_sample_docs.py
```

## Local OCR Requirements

- `pytesseract` Python package is already in requirements.
- Tesseract OCR binary must be installed on the host and available on PATH.
- For PDF conversion on Windows, `pdf2image` may require Poppler binaries available on PATH.

## Quick Test Flow

1. Generate sample docs using the script.
2. Start API service.
3. Call `POST /ocr/upload` in Swagger UI.
4. Confirm extracted fields and confidence values.
5. Call `POST /ocr/upload-and-create` with ids to create a billing record.
