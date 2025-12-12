from abc import ABC, abstractmethod
import os
import logging
import fitz  # PyMuPDF
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, file_path: str, doc_id: str = "temp") -> str:
        pass
    
    @abstractmethod
    def get_page_count(self, file_path: str) -> int:
        pass
    
    @abstractmethod
    def extract_page(self, file_path: str, page_number: int) -> str:
        pass


class OpenAIOCRService(OCRProvider):
    """
    Service OCR qui utilise l'API OpenAI pour extraire
    et convertir le contenu d'un PDF en HTML structuré.
    Supporte le lazy loading page par page.
    """

    EXTRACTION_PROMPT = """Act as an expert data extractor and web developer. I am providing a PDF document (single page). Your goal is to convert the visual content of this PDF into a clean, semantically correct HTML structure.

Instructions:

Analyze the layout: Identify headers, paragraphs, lists, and data tables.

Structure: Use appropriate HTML5 tags (<h1>, <h2>, <p>, <ul>, <table>, <thead>, <tbody>).

Tables: If the PDF contains grids or tables, you MUST reconstruct them using HTML <table> tags with proper row/column alignment. Do not list table data as plain text.

Styling: Do NOT include any <style> tags or CSS rules. Do NOT style the body element. Only use minimal inline styles on specific elements if absolutely necessary for table borders.

Output: Return ONLY the raw HTML content (no <html>, <head>, <body> wrapper tags). No markdown code blocks (```html) or conversational filler."""

    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            logger.warning("OpenAI API key not found in settings")
            self.client = None
        else:
            logger.info(f"OpenAI API key loaded (starts with: {api_key[:20]}...)")
            self.client = OpenAI(api_key=api_key)
    
    def get_page_count(self, file_path: str) -> int:
        """Retourne le nombre de pages du PDF."""
        logger.info(f"Obtention du nombre de pages pour {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        doc = fitz.open(file_path)
        count = len(doc)
        doc.close()
        return count
    
    def _extract_single_page_pdf(self, file_path: str, page_number: int) -> str:
        """
        Extrait une seule page du PDF et la sauvegarde temporairement.
        page_number est 0-indexed.
        Retourne le chemin du fichier temporaire.
        """
        logger.info(f"Extraction de la page {page_number} du PDF {file_path}")
        doc = fitz.open(file_path)
        
        if page_number < 0 or page_number >= len(doc):
            doc.close()
            raise ValueError(f"Page {page_number} out of range (0-{len(doc)-1})")
        
        # Créer un nouveau PDF avec juste cette page
        single_page_doc = fitz.open()
        single_page_doc.insert_pdf(doc, from_page=page_number, to_page=page_number)
        
        # Sauvegarder temporairement
        temp_path = f"/tmp/page_{page_number}_{os.path.basename(file_path)}"
        single_page_doc.save(temp_path)
        single_page_doc.close()
        doc.close()
        
        return temp_path

    def extract_page(self, file_path: str, page_number: int) -> str:
        """
        Extrait une seule page du PDF en utilisant l'API OpenAI.
        page_number est 0-indexed.
        """
        logger.info(f"Début extraction page {page_number} de {file_path}")
        if not self.client:
            raise ValueError("OpenAI API key not configured. Please set SECRET_KEY in .env")
        
        try:
            logger.info(f"Extraction page {page_number} de {file_path}")
            
            # Vérifier que le fichier existe
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            # Extraire la page unique dans un PDF temporaire
            temp_pdf_path = self._extract_single_page_pdf(file_path, page_number)
            
            try:
                # 1. Upload du fichier PDF (page unique) à OpenAI
                logger.info(f"Upload de la page {page_number} vers OpenAI...")
                with open(temp_pdf_path, "rb") as pdf_file:
                    uploaded_file = self.client.files.create(
                        file=pdf_file,
                        purpose="assistants"
                    )
                logger.info(f"Page uploadée avec ID: {uploaded_file.id}")

                # 2. Appeler l'API responses avec le fichier
                logger.info("Appel de l'API OpenAI pour extraction...")
                response = self.client.responses.create(
                    model="gpt-4o",
                    input=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_file",
                                    "file_id": uploaded_file.id,
                                },
                                {
                                    "type": "input_text",
                                    "text": self.EXTRACTION_PROMPT,
                                },
                            ]
                        }
                    ]
                )

                # 3. Récupérer le contenu HTML
                html_content = response.output_text
                logger.info(f"Réponse reçue: {len(html_content)} caractères")

                # 4. Nettoyer la réponse
                html_content = self._clean_html_response(html_content)

                # 5. Supprimer le fichier uploadé (nettoyage)
                try:
                    self.client.files.delete(uploaded_file.id)
                    logger.info(f"Fichier {uploaded_file.id} supprimé de OpenAI")
                except Exception as e:
                    logger.warning(f"Impossible de supprimer le fichier uploadé: {e}")

                logger.info(f"Page {page_number} extraite: {len(html_content)} chars")
                return html_content
                
            finally:
                # Nettoyer le fichier temporaire
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)

        except Exception as e:
            logger.error(f"Erreur extraction page {page_number}: {type(e).__name__}: {e}", exc_info=True)
            raise

    def extract_text(self, file_path: str, doc_id: str = "temp") -> str:
        """
        Extrait uniquement la première page pour initialiser le document.
        Les autres pages seront extraites à la demande (lazy loading).
        """
        return self.extract_page(file_path, 0)

    def _clean_html_response(self, response: str) -> str:
        """
        Nettoie la réponse de l'API en supprimant les éventuels blocs de code markdown
        et les styles indésirables sur body.
        """
        if not response:
            return ""

        response = response.strip()

        if response.startswith("```html"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()
        
        # Supprimer les balises <style> qui pourraient affecter le body global
        import re
        # Supprimer tout bloc <style> contenant body { ... }
        response = re.sub(r'<style[^>]*>.*?body\s*\{[^}]*\}.*?</style>', '', response, flags=re.DOTALL | re.IGNORECASE)
        # Supprimer les styles body inline restants
        response = re.sub(r'body\s*\{[^}]*margin[^}]*\}', '', response, flags=re.IGNORECASE)
        
        return response


def get_ocr_service() -> OpenAIOCRService:
    """Retourne le service OCR par défaut (OpenAI)."""
    return OpenAIOCRService()
