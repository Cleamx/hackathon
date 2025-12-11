from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.document import Document, ProcessingStatus
from app.services.storage import StorageService
from app.services.ocr.service import get_ocr_service
import shutil
import logging
import os
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

async def process_document(document_id: int, file_path: str):
    """
    Traitement initial du document : compte les pages et extrait la première page.
    Les autres pages seront extraites à la demande (lazy loading).
    """
    logger.info(f"Background task started for doc {document_id} at {file_path}")
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

            ocr_service = get_ocr_service()
            loop = asyncio.get_running_loop()
            
            # 1. Compter les pages du PDF
            page_count = await loop.run_in_executor(None, ocr_service.get_page_count, file_path)
            document.page_count = page_count
            document.extracted_pages = {}
            logger.info(f"Document {document_id} has {page_count} pages")
            
            # 2. Extraire uniquement la première page
            logger.info(f"Extracting first page for doc {document_id}")
            first_page_html = await loop.run_in_executor(None, ocr_service.extract_page, file_path, 0)
            
            # Stocker la première page
            document.extracted_pages = {"0": first_page_html}
            document.extracted_text = first_page_html  # Compatibilité legacy
            document.status = ProcessingStatus.COMPLETED.value
            
            await session.commit()
            logger.info(f"Document {document_id} first page processed successfully")

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

@router.get("/", response_model=list[dict])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.upload_date.desc()))
    documents = result.scalars().all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "upload_date": doc.upload_date
        }
        for doc in documents
    ]

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
        "upload_date": document.upload_date,
        "page_count": document.page_count
    }

import re

@router.get("/{document_id}/text")
async def get_document_text(document_id: int, db: AsyncSession = Depends(get_db)):
    """Retourne les informations sur les pages extraites."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != ProcessingStatus.COMPLETED.value:
         raise HTTPException(status_code=400, detail=f"Document is not ready. Status: {document.status}")

    # Retourner les pages extraites
    extracted_pages = document.extracted_pages or {}
    
    # Construire la liste des pages (avec None pour les non-extraites)
    pages = []
    for i in range(document.page_count or 1):
        page_content = extracted_pages.get(str(i))
        pages.append(page_content)  # None si pas encore extrait
    
    return {
        "page_count": document.page_count or 1,
        "pages": pages,
        "extracted_pages": list(extracted_pages.keys()),  # Liste des pages déjà extraites
        "summary": document.summary
    }

@router.get("/{document_id}/page/{page_number}")
async def get_page(document_id: int, page_number: int, db: AsyncSession = Depends(get_db)):
    """
    Récupère une page spécifique. Si pas encore extraite, lance l'extraction.
    page_number est 0-indexed.
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != ProcessingStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail=f"Document is not ready. Status: {document.status}")
    
    if page_number < 0 or page_number >= (document.page_count or 1):
        raise HTTPException(status_code=400, detail=f"Invalid page number. Document has {document.page_count} pages (0-{document.page_count-1})")
    
    extracted_pages = document.extracted_pages or {}
    page_key = str(page_number)
    
    # Vérifier si la page est déjà extraite
    if page_key in extracted_pages:
        return {"page_number": page_number, "content": extracted_pages[page_key], "cached": True}
    
    # Sinon, extraire la page
    try:
        ocr_service = get_ocr_service()
        loop = asyncio.get_running_loop()
        
        logger.info(f"Extracting page {page_number} for document {document_id}")
        page_html = await loop.run_in_executor(
            None, 
            ocr_service.extract_page, 
            document.file_path, 
            page_number
        )
        
        # Sauvegarder la page extraite
        extracted_pages[page_key] = page_html
        document.extracted_pages = extracted_pages
        await db.commit()
        
        logger.info(f"Page {page_number} extracted and cached for document {document_id}")
        return {"page_number": page_number, "content": page_html, "cached": False}
        
    except Exception as e:
        logger.error(f"Error extracting page {page_number} for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract page: {str(e)}")

@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete file from storage
    if document.file_path and os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except OSError:
            logger.warning(f"Could not remove file {document.file_path}")

    # Delete from DB
    await db.delete(document)
    await db.commit()
    return None
