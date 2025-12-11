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
async def test_upload_document_success(client: AsyncClient):
    # Mock PDF content
    files = {"file": ("test.pdf", io.BytesIO(b"%PDF-1.4..."), "application/pdf")}
    response = await client.post("/api/documents/", files=files)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"
    return data["id"]
