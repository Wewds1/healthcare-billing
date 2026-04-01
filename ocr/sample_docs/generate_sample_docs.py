from __future__ import annotations

from pathlib import Path
from random import randint, uniform

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE_DIR = Path(__file__).resolve().parent

TEMPLATES = {
    "insurance_claim": [
        "Patient Name: John Carter",
        "DOB: 04/17/1978",
        "Insurance ID: INS-449812",
        "CPT: 99213, 93000",
        "ICD-10: E11.9",
        "Billed Amount: $245.60",
        "Provider NPI: 1234567890",
    ],
    "invoice": [
        "Invoice Number: HINV-2026-001",
        "Invoice Date: 03/21/2026",
        "Line Item: MRI Scan $550.00",
        "Line Item: Lab Panel $180.50",
        "Tax: $21.95",
        "Total: $752.45",
    ],
    "patient_id": [
        "Patient Name: Alicia Monroe",
        "Member ID: MEM-772910",
        "Group Number: GRP-5531",
        "Effective Date: 01/01/2026",
        "Copay PCP: $25",
        "Copay Specialist: $45",
    ],
    "handwritten": [
        "Follow-up needed in 2 weeks",
        "A1C value 8.1",
        "Blood pressure 138/88",
        "Possible claim amount 125.00",
        "Manual review suggested",
    ],
}


def _variant_lines(lines: list[str]) -> list[str]:
    updated = []
    for line in lines:
        if "$" in line:
            value = round(uniform(50.0, 950.0), 2)
            updated.append(line.split("$")[0] + f"${value:,.2f}")
        elif "2026" in line:
            updated.append(line.replace("2026", str(randint(2024, 2026))))
        else:
            updated.append(line)
    return updated


def _build_image(lines: list[str], skew: int = 0, blur: bool = False, low_contrast: bool = False) -> Image.Image:
    background = (245, 245, 245) if low_contrast else (255, 255, 255)
    text_color = (90, 90, 90) if low_contrast else (15, 15, 15)

    img = Image.new("RGB", (1654, 2339), color=background)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 44)
        title_font = ImageFont.truetype("arial.ttf", 58)
    except OSError:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    draw.text((110, 90), "Healthcare Billing Sample", fill=text_color, font=title_font)

    y = 260
    for line in lines:
        draw.text((120, y), line, fill=text_color, font=font)
        y += 90

    if skew != 0:
        img = img.rotate(skew, expand=True, fillcolor=background)

    if blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=1.1))

    return img.convert("RGB")


def generate_samples() -> None:
    variant_settings = [
        {"name": "sample_1_clear", "skew": 0, "blur": False, "low_contrast": False},
        {"name": "sample_2_skewed", "skew": 3, "blur": False, "low_contrast": False},
        {"name": "sample_3_low_quality", "skew": 0, "blur": True, "low_contrast": True},
    ]

    for doc_type, lines in TEMPLATES.items():
        target_dir = BASE_DIR / doc_type
        target_dir.mkdir(parents=True, exist_ok=True)

        for setting in variant_settings:
            prepared_lines = _variant_lines(lines)
            image = _build_image(
                prepared_lines,
                skew=setting["skew"],
                blur=setting["blur"],
                low_contrast=setting["low_contrast"],
            )
            output_file = target_dir / f"{setting['name']}.pdf"
            image.save(output_file, "PDF", resolution=300.0)

    print(f"Sample PDFs created under: {BASE_DIR}")


if __name__ == "__main__":
    generate_samples()
