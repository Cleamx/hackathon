from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.document import Document

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/reader/{document_id}")
async def reader(request: Request, document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Document not found"})
        
    response = templates.TemplateResponse("reader.html", {
        "request": request,
        "document": document
    })
    # Disable caching to ensure JS updates are seen
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get("/library")
async def library(request: Request):
    return templates.TemplateResponse("library.html", {"request": request})

@router.get("/accessibility")
async def accessibility(request: Request):
    return templates.TemplateResponse("accessibility.html", {"request": request})
