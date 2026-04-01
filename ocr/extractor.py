from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import cv2
import pytesseract
from pytesseract import Output


CONFIGS: Dict[str, str] = {
	"insurance_claim": "--psm 6 --oem 3",
	"invoice": "--psm 4 --oem 3",
	"patient_id": "--psm 7 --oem 3",
	"handwritten": "--psm 6 --oem 1",
}


def _mean_confidence(data: dict) -> float:
	scores = []
	for value in data.get("conf", []):
		try:
			score = float(value)
		except (TypeError, ValueError):
			continue
		if score >= 0:
			scores.append(score)
	if not scores:
		return 0.0
	return round(sum(scores) / len(scores), 2)


def extract_text(
	processed_image,
	document_type: str,
	rois: Optional[List[Tuple[int, int, int, int]]] = None,
) -> dict:
	"""Run Tesseract OCR on the full image and optionally on ROI regions."""
	if document_type not in CONFIGS:
		raise ValueError(f"Unsupported document_type '{document_type}'")

	config = CONFIGS[document_type]

	try:
		full_data = pytesseract.image_to_data(processed_image, config=config, output_type=Output.DICT)
	except pytesseract.pytesseract.TesseractNotFoundError as exc:
		raise RuntimeError("Tesseract binary not found. Install Tesseract and add it to PATH.") from exc

	full_text = " ".join(t for t in full_data.get("text", []) if t and t.strip()).strip()
	segments = []

	if rois:
		for idx, (x, y, w, h) in enumerate(rois[:25]):
			crop = processed_image[y : y + h, x : x + w]
			if crop.size == 0:
				continue
			roi_data = pytesseract.image_to_data(crop, config=config, output_type=Output.DICT)
			text = " ".join(t for t in roi_data.get("text", []) if t and t.strip()).strip()
			if text:
				segments.append(
					{
						"roi_index": idx,
						"bbox": [x, y, w, h],
						"text": text,
						"confidence": _mean_confidence(roi_data),
					}
				)

	return {
		"raw_text": full_text,
		"overall_confidence": _mean_confidence(full_data),
		"segments": segments,
	}
