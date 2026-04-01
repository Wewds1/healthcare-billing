from __future__ import annotations

import re
from typing import Any, Dict, List


def _find_first(patterns: List[str], text: str) -> str | None:
	for pattern in patterns:
		match = re.search(pattern, text, flags=re.IGNORECASE)
		if match:
			return match.group(1).strip()
	return None


def _find_all(pattern: str, text: str) -> List[str]:
	return [match.strip() for match in re.findall(pattern, text, flags=re.IGNORECASE)]


def parse_fields(raw_text: str, document_type: str) -> Dict[str, Any]:
	"""Parse OCR text into structured fields and simple confidence hints."""
	normalized = raw_text.replace("\n", " ")

	fields: Dict[str, Any] = {}
	confidence: Dict[str, float] = {}

	if document_type == "insurance_claim":
		fields["patient_name"] = _find_first([r"patient\s*name[:\-]\s*([A-Za-z\s,.'-]{3,})"], normalized)
		fields["dob"] = _find_first([r"(?:dob|date\s*of\s*birth)[:\-]\s*([0-9/\-]{8,10})"], normalized)
		fields["insurance_id"] = _find_first([r"(?:insurance|member)\s*id[:\-]\s*([A-Z0-9\-]{5,})"], normalized)
		fields["cpt_codes"] = _find_all(r"\b(\d{5})\b", normalized)
		fields["icd10_codes"] = _find_all(r"\b([A-TV-Z][0-9][0-9A-Z](?:\.[0-9A-Z]{1,4})?)\b", normalized)
		amount = _find_first([r"(?:billed\s*amount|amount\s*due|total)[:\-]?\s*\$?([0-9]+(?:\.[0-9]{2})?)"], normalized)
		fields["billed_amount"] = float(amount) if amount else None

	elif document_type == "invoice":
		fields["invoice_number"] = _find_first([r"(?:invoice\s*#|invoice\s*number)[:\-]\s*([A-Z0-9\-]+)"], normalized)
		fields["invoice_date"] = _find_first([r"(?:invoice\s*date|date)[:\-]\s*([0-9/\-]{8,10})"], normalized)
		amount = _find_first([r"(?:total|amount\s*due)[:\-]?\s*\$?([0-9]+(?:\.[0-9]{2})?)"], normalized)
		fields["total_amount"] = float(amount) if amount else None
		fields["line_item_amounts"] = [float(x) for x in _find_all(r"\$([0-9]+(?:\.[0-9]{2})?)", normalized)]

	elif document_type == "patient_id":
		fields["member_id"] = _find_first([r"(?:member\s*id|id)[:\-]\s*([A-Z0-9\-]{5,})"], normalized)
		fields["group_number"] = _find_first([r"(?:group\s*(?:no|number))[:\-]\s*([A-Z0-9\-]{3,})"], normalized)
		fields["patient_name"] = _find_first([r"(?:name|patient)[:\-]\s*([A-Za-z\s,.'-]{3,})"], normalized)
		fields["effective_date"] = _find_first([r"(?:effective\s*date|eff\.?\s*date)[:\-]\s*([0-9/\-]{8,10})"], normalized)

	elif document_type == "handwritten":
		numeric = _find_all(r"([0-9]+(?:\.[0-9]{2})?)", normalized)
		fields["manual_review_required"] = True
		fields["numbers_detected"] = numeric

	else:
		raise ValueError(f"Unsupported document_type '{document_type}'")

	for key, value in fields.items():
		if value in (None, "", []):
			confidence[key] = 0.0
		elif isinstance(value, list):
			confidence[key] = 0.75
		else:
			confidence[key] = 0.9

	return {
		"extracted_fields": fields,
		"confidence_scores": confidence,
	}
