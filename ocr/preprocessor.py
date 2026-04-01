from __future__ import annotations

from io import BytesIO
from typing import List, Tuple

import cv2
import numpy as np
from pdf2image import convert_from_bytes
from PIL import Image


def load_document(file_bytes: bytes, filename: str) -> np.ndarray:
	"""Load an image or PDF document into an OpenCV BGR image."""
	lower_name = filename.lower()

	if lower_name.endswith(".pdf"):
		pages = convert_from_bytes(file_bytes, dpi=300)
		if not pages:
			raise ValueError("PDF did not contain any pages")
		pil_image = pages[0].convert("RGB")
	else:
		pil_image = Image.open(BytesIO(file_bytes)).convert("RGB")

	return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)


def _deskew(gray_image: np.ndarray) -> np.ndarray:
	inverted = cv2.bitwise_not(gray_image)
	threshold = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
	coords = np.column_stack(np.where(threshold > 0))

	if coords.size == 0:
		return gray_image

	angle = cv2.minAreaRect(coords)[-1]
	if angle < -45:
		angle = -(90 + angle)
	else:
		angle = -angle

	(h, w) = gray_image.shape[:2]
	center = (w // 2, h // 2)
	matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
	return cv2.warpAffine(gray_image, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def _detect_rois(binary_image: np.ndarray) -> List[Tuple[int, int, int, int]]:
	contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	rois: List[Tuple[int, int, int, int]] = []

	height, width = binary_image.shape[:2]
	min_area = max(250, int((height * width) * 0.0004))

	for contour in contours:
		x, y, w, h = cv2.boundingRect(contour)
		if w * h >= min_area:
			rois.append((x, y, w, h))

	rois.sort(key=lambda r: (r[1], r[0]))
	return rois


def preprocess_document(image_bgr: np.ndarray) -> Tuple[np.ndarray, List[Tuple[int, int, int, int]]]:
	"""Apply OCR-friendly preprocessing and return a clean binary image and ROIs."""
	gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
	resized = cv2.resize(gray, None, fx=1.3, fy=1.3, interpolation=cv2.INTER_CUBIC)
	deskewed = _deskew(resized)

	denoised = cv2.fastNlMeansDenoising(deskewed, None, h=12, templateWindowSize=7, searchWindowSize=21)
	thresholded = cv2.adaptiveThreshold(
		denoised,
		255,
		cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
		cv2.THRESH_BINARY,
		31,
		11,
	)

	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
	cleaned = cv2.morphologyEx(thresholded, cv2.MORPH_OPEN, kernel)
	rois = _detect_rois(255 - cleaned)
	return cleaned, rois
