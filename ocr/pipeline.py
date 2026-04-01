from __future__ import annotations

import base64
from typing import Any, Dict

import cv2

from ocr.extractor import extract_text
from ocr.parser import parse_fields
from ocr.preprocessor import load_document, preprocess_document


class OCRPipeline:
	"""Orchestrates preprocessing, OCR extraction, and field parsing."""

	def run(self, file_bytes: bytes, filename: str, document_type: str) -> Dict[str, Any]:
		image = load_document(file_bytes=file_bytes, filename=filename)
		processed_image, rois = preprocess_document(image)
		ocr_result = extract_text(processed_image=processed_image, document_type=document_type, rois=rois)
		parsed = parse_fields(raw_text=ocr_result["raw_text"], document_type=document_type)

		success, encoded = cv2.imencode(".png", processed_image)
		if not success:
			preprocessed_b64 = None
		else:
			preprocessed_b64 = base64.b64encode(encoded.tobytes()).decode("utf-8")

		return {
			**parsed,
			"raw_text": ocr_result["raw_text"],
			"overall_confidence": ocr_result["overall_confidence"],
			"segments": ocr_result["segments"],
			"preprocessed_image_base64": preprocessed_b64,
			"roi_count": len(rois),
		}


def get_ocr_pipeline() -> OCRPipeline:
	return OCRPipeline()
