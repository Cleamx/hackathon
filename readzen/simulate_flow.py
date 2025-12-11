import asyncio
import httpx
import os
import sys

# Create a dummy PDF
def create_dummy_pdf():
    with open("sim_test.pdf", "wb") as f:
        f.write(b"%PDF-1.4\n%...\n") # Minimal header, likely invalid for real OCR but good for upload testing.
        # process_document checks for valid PDF structure usually, so let's make it slightly more real if possible, 
        # or rely on the backend gracefully failing invalid PDFs. 
        # Actually, let's use the fpdf one if we can, or just a text file renamed.
        # Using a text file renamed might trigger "Syntax Error" in pdf2image but should handle it.
        f.write(b"Not a real PDF but enough bytes.\n" * 100)

async def run_simulation():
    create_dummy_pdf()
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        print("1. Uploading document...")
        files = {'file': ('sim_test.pdf', open('sim_test.pdf', 'rb'), 'application/pdf')}
        res = await client.post("/api/documents/", files=files)
        print(f"Upload Status: {res.status_code}")
        if res.status_code != 202:
            print(res.text)
            sys.exit(1)
            
        doc_id = res.json()['id']
        print(f"Document ID: {doc_id}")
        
        print("2. Polling status...")
        for i in range(30):
            res = await client.get(f"/api/documents/{doc_id}")
            data = res.json()
            status = data['status']
            print(f"Poll {i}: {status}")
            
            if status == 'completed':
                print("SUCCESS: Document processed.")
                break
            elif status == 'failed':
                print("FAILURE: Processing failed (as expected for dummy PDF, but pipeline works).")
                break
            
            await asyncio.sleep(1)
        else:
            print("TIMEOUT: Document stuck in pending/processing.")

if __name__ == "__main__":
    asyncio.run(run_simulation())
