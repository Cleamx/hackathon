from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.document import Document, ProcessingStatus
from app.services.storage import StorageService
from app.services.ocr.service import get_ocr_service
import shutil
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def process_document(document_id: int, file_path: str):
    # Re-creating session because the request session is closed.
    from app.core.database import SessionLocal
    async with SessionLocal() as session:
        stmt = select(Document).where(Document.id == document_id)
        result = await session.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            logger.error(f"Document {document_id} not found in background task")
            return

        try:
            document.status = ProcessingStatus.PROCESSING.value
            await session.commit()

            # OCR Processing
            ocr_service = get_ocr_service()
            # Running synchronous OCR in a threadpool to not block the event loop
            import asyncio
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(None, ocr_service.extract_text, file_path)

            document.extracted_text = text
            document.status = ProcessingStatus.COMPLETED.value
            await session.commit()
            logger.info(f"Document {document_id} processed successfully")

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            document.status = ProcessingStatus.FAILED.value
            await session.commit()

@router.post("/", status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Create DB entry
    new_doc = Document(filename=file.filename, status=ProcessingStatus.PENDING.value)
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    doc_id = new_doc.id

    # Save file
    try:
        file_path = await StorageService.save_upload(file, f"{doc_id}_{file.filename}")
        new_doc.file_path = file_path
        await db.commit()
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        await db.delete(new_doc)
        await db.commit()
        raise HTTPException(status_code=500, detail="File upload failed")

    # Trigger background task
    background_tasks.add_task(process_document, doc_id, file_path)

    return {"id": doc_id, "status": ProcessingStatus.PENDING.value}

@router.get("/{document_id}")
async def get_document(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": document.id,
        "filename": document.filename,
        "status": document.status,
        "upload_date": document.upload_date
    }

@router.get("/{document_id}/text")
async def get_document_text(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != ProcessingStatus.COMPLETED.value:
         raise HTTPException(status_code=400, detail=f"Document is not ready. Status: {document.status}")

    return {"text": document.extracted_text}
