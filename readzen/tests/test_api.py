import pytest
from httpx import AsyncClient
import io

@pytest.mark.anyio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "readzen"}

@pytest.mark.anyio
async def test_upload_document_invalid_type(client: AsyncClient):
    files = {"file": ("test.txt", io.BytesIO(b"test content"), "text/plain")}
    response = await client.post("/api/documents/", files=files)
    assert response.status_code == 400
    assert "Only PDF files" in response.json()["detail"]

@pytest.mark.anyio
async def test_upload_document(client, test_db, tmp_path):
    # Prepare dummy PDF
    pdf_content = b"%PDF-1.4 header"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    
    response = await client.post("/api/documents/", files=files)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.main import app
from app.core.database import get_db, Base

@pytest.mark.anyio
async def test_delete_document(client, test_db):
    # 1. Create a document directly in DB
    from app.models.document import Document
    new_doc = Document(filename="todelete.pdf", status="completed", file_path="/tmp/dummy")
    test_db.add(new_doc)
    await test_db.commit()
    await test_db.refresh(new_doc)
    doc_id = new_doc.id

    # 2. Delete it via API
    response = await client.delete(f"/api/documents/{doc_id}")
    assert response.status_code == 204
    
    # 3. Verify it's gone
    result = await test_db.execute(select(Document).where(Document.id == doc_id))
    assert result.scalar_one_or_none() is None
