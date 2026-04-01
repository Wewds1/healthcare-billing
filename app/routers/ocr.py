from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.rbac import require_admin, require_user
from app.crud import billing_record as billing_crud
from app.schemas.billing_record import BillingRecordCreate
from ocr.pipeline import get_ocr_pipeline

router = APIRouter(prefix="/ocr", tags=["ocr"])

SUPPORTED_DOCUMENT_TYPES = {"insurance_claim", "invoice", "patient_id", "handwritten"}


@router.post("/upload")
async def upload_document_for_ocr(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(require_user),
):
    if document_type not in SUPPORTED_DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported document_type")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    pipeline = get_ocr_pipeline()
    try:
        result = pipeline.run(file_bytes=content, filename=file.filename or "upload", document_type=document_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(exc)}") from exc

    return result


@router.post("/upload-and-create")
async def upload_and_create_billing_record(
    document_type: str = Form(...),
    patient_id: int = Form(...),
    procedure_id: int = Form(...),
    status: str = Form("pending"),
    diagnosis_code: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if document_type not in SUPPORTED_DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported document_type")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    pipeline = get_ocr_pipeline()
    try:
        ocr_result = pipeline.run(file_bytes=content, filename=file.filename or "upload", document_type=document_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(exc)}") from exc

    extracted = ocr_result.get("extracted_fields", {})
    amount_value = extracted.get("billed_amount") or extracted.get("total_amount")
    amount = float(amount_value) if amount_value is not None else 0.0

    record_payload = BillingRecordCreate(
        patient_id=patient_id,
        procedure_id=procedure_id,
        amount=amount,
        status=status,
        diagnosis_code=diagnosis_code,
    )

    created = billing_crud.create_billing_record(db=db, billing_record=record_payload)
    return {
        "ocr_result": ocr_result,
        "created_billing_record_id": created.id,
    }
