# ReadZen

ReadZen is a modular, accessible, and mobile-friendly web prototype for reading PDF documents in a reflowable text format.

## Features
- **Reflowable Text**: Converts PDFs to easy-to-read text.
- **Accessibility**: Dyslexic fonts, themes (Light/Dark/Sepia).
- **Mobile-Friendly**: Responsive design.
- **OCR Support**: Handles scanned documents.

## Tech Stack
- **Backend**: FastAPI, SQLite, SQLAlchemy.
- **OCR**: Tesseract, pdf2image.
- **Frontend**: HTML/CSS (Jinja2), No JS framework.
- **DevOps**: Docker, Docker Compose.

## Getting Started

### Prerequisites
- Docker & Docker Compose

### Running the App
1. Build and start the container:
   ```bash
   docker-compose up --build
   ```
2. Access the application at `http://localhost:8000`.
3. API Documentation available at `http://localhost:8000/docs`.

## Development
- Tests: `pytest`
- Code structure is in `app/`.
