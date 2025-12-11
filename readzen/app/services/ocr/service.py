from abc import ABC, abstractmethod
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageOps
import fitz  # PyMuPDF
import os
import logging
import re
import hashlib
import shutil

logger = logging.getLogger(__name__)

import pymupdf4llm


class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, file_path: str, doc_id: str = "temp") -> str:
        pass


class PyMuPDF4LLMService(OCRProvider):
    """
    Service OCR qui préserve la mise en page originale du PDF.
    Extrait le texte avec les informations d'alignement et de structure.
    Filtre automatiquement les headers et footers.
    """
    
    # Patterns pour détecter les headers/footers à filtrer
    HEADER_FOOTER_PATTERNS = [
        # Numéros de page
        r'^\s*\d+\s*$',
        r'^\s*-\s*\d+\s*-\s*$',
        r'^\s*Page\s+\d+\s*$',
        # Copyright et DOI
        r'©\s*\d{4}',
        r'https?://doi\.org/',
        r'ACM\s+ISBN',
        r'978-\d+-\d+-\d+-\d+',
        r'979-\d+-\d+-\d+-\d+',
        # Conférences/Journaux (lignes courtes avec dates et lieux)
        r"^[A-Z]{2,}['\s]\d{2},?\s*(January|February|March|April|May|June|July|August|September|October|November|December|\d{1,2}[-–]\d{1,2})",
        r'^\s*[A-Z][a-z]+\s+\d{1,2}[-–]\d{1,2},\s*\d{4}',
        # Headers répétitifs de journaux
        r'^(Vol\.|Volume)\s*\d+',
        r'^(No\.|Number)\s*\d+',
        r'^\s*ISSN\s*\d',
        # Lignes avec seulement des infos de publication
        r'^Copyright\s+held\s+by',
        r'^Permission\s+to\s+make',
        r'^This\s+work\s+is\s+licensed',
    ]
    
    def __init__(self):
        self.header_footer_regexes = [re.compile(p, re.IGNORECASE) for p in self.HEADER_FOOTER_PATTERNS]
    
    def extract_text(self, file_path: str, doc_id: str = "temp") -> str:
        """
        Extrait le texte d'un PDF en préservant la mise en page.
        Génère du HTML avec les styles d'alignement appropriés.
        """
        try:
            logger.info(f"Extraction avec mise en page pour {file_path}")
            
            # Dossier pour les images
            img_rel_path = f"images/{doc_id}"
            img_output_dir = os.path.join("app/static/uploads", img_rel_path)
            
            if os.path.exists(img_output_dir):
                shutil.rmtree(img_output_dir)
            os.makedirs(img_output_dir, exist_ok=True)
            
            # Ouvrir le PDF
            doc = fitz.open(file_path)
            all_pages_html = []
            
            for page_num in range(len(doc)):
                logger.info(f"Traitement page {page_num + 1}/{len(doc)}")
                page = doc[page_num]
                
                # Extraire avec informations de mise en page
                page_html = self._extract_page_with_layout(page, page_num, img_output_dir, img_rel_path)
                
                if page_html.strip():
                    all_pages_html.append(f"\n\n--- Page {page_num + 1} ---\n\n{page_html}")
            
            doc.close()
            
            final_text = ''.join(all_pages_html)
            logger.info(f"Extraction terminée: {len(final_text)} chars, {len(all_pages_html)} pages")
            
            return final_text
            
        except Exception as e:
            logger.error(f"Erreur extraction: {e}")
            raise
    
    def _is_header_or_footer(self, text: str, block_bbox: list, page_height: float) -> bool:
        """
        Détermine si un bloc est un header ou footer à filtrer.
        """
        if not text or not text.strip():
            return True
        
        text_clean = text.strip()
        
        # Vérifier la position (haut ou bas de page)
        y0 = block_bbox[1]
        y1 = block_bbox[3]
        
        # Zone header (top 8% de la page) ou footer (bottom 10% de la page)
        is_in_header_zone = y0 < page_height * 0.08
        is_in_footer_zone = y1 > page_height * 0.90
        
        # Si c'est dans une zone header/footer, vérifier le contenu
        if is_in_header_zone or is_in_footer_zone:
            # Texte très court dans ces zones = probablement header/footer
            if len(text_clean) < 100:
                # Vérifier les patterns
                for regex in self.header_footer_regexes:
                    if regex.search(text_clean):
                        return True
                
                # Numéro de page seul
                if text_clean.isdigit():
                    return True
        
        # Vérifier les patterns même en dehors des zones
        for regex in self.header_footer_regexes:
            if regex.search(text_clean):
                # Seulement filtrer si c'est une ligne courte
                if len(text_clean) < 150:
                    return True
        
        return False
    
    def _extract_page_with_layout(self, page: fitz.Page, page_num: int, img_output_dir: str, img_rel_path: str) -> str:
        """
        Extrait une page en préservant la mise en page (alignement, structure).
        Filtre les headers et footers.
        """
        page_width = page.rect.width
        page_height = page.rect.height
        page_center = page_width / 2
        
        # Extraire les blocs de texte avec leurs positions
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        
        html_parts = []
        
        for block in blocks:
            if block["type"] == 0:  # Bloc de texte
                # Extraire le texte brut pour vérifier si c'est un header/footer
                block_text = self._get_block_text(block)
                block_bbox = block.get("bbox", [0, 0, page_width, page_height])
                
                # Filtrer les headers/footers
                if self._is_header_or_footer(block_text, block_bbox, page_height):
                    logger.debug(f"Filtered header/footer: {block_text[:50]}...")
                    continue
                
                block_html = self._process_text_block(block, page_width, page_center)
                if block_html:
                    html_parts.append(block_html)
            elif block["type"] == 1:  # Bloc image
                img_html = self._process_image_block(block, page_num, img_output_dir, img_rel_path)
                if img_html:
                    html_parts.append(img_html)
        
        return '\n'.join(html_parts)
    
    def _get_block_text(self, block: dict) -> str:
        """Extrait le texte brut d'un bloc."""
        text_parts = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text_parts.append(span.get("text", ""))
        return ' '.join(text_parts)
    
    def _process_text_block(self, block: dict, page_width: float, page_center: float) -> str:
        """
        Traite un bloc de texte et détermine son alignement.
        """
        lines = block.get("lines", [])
        if not lines:
            return ""
        
        # Collecter tout le texte du bloc
        block_text_parts = []
        block_x0 = block.get("bbox", [0])[0]
        block_x1 = block.get("bbox", [0, 0, page_width])[2]
        block_width = block_x1 - block_x0
        
        # Analyser les propriétés des lignes
        is_title = False
        is_bold = False
        font_sizes = []
        
        for line in lines:
            line_text = ""
            for span in line.get("spans", []):
                text = span.get("text", "")
                font_size = span.get("size", 12)
                font_flags = span.get("flags", 0)
                
                font_sizes.append(font_size)
                
                # Détecter gras (flag 2^4 = 16 pour bold)
                if font_flags & 16:
                    is_bold = True
                
                line_text += text
            
            if line_text.strip():
                block_text_parts.append(line_text)
        
        if not block_text_parts:
            return ""
        
        full_text = '\n'.join(block_text_parts)
        
        # Nettoyer le texte
        full_text = self._clean_text(full_text)
        
        if not full_text.strip():
            return ""
        
        # Déterminer l'alignement basé sur la position du bloc
        alignment = self._detect_alignment(block, page_width, page_center)
        
        # Déterminer si c'est un titre (texte court, centré ou tout en majuscules)
        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
        is_title = (
            (full_text.isupper() and len(full_text) < 100) or
            (avg_font_size > 14 and len(full_text) < 150) or
            (alignment == "center" and len(full_text) < 100)
        )
        
        # Générer le HTML avec le bon style
        style_parts = []
        
        if alignment == "center":
            style_parts.append("text-align: center")
        elif alignment == "right":
            style_parts.append("text-align: right")
        elif alignment == "justify":
            style_parts.append("text-align: justify")
        else:
            style_parts.append("text-align: left")
        
        style = "; ".join(style_parts) if style_parts else ""
        
        # Échapper le HTML dans le texte
        escaped_text = full_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Convertir les sauts de ligne en <br>
        escaped_text = escaped_text.replace("\n", "<br>")
        
        if is_title:
            if full_text.isupper():
                return f'<h2 style="{style}">{escaped_text}</h2>'
            else:
                return f'<h3 style="{style}">{escaped_text}</h3>'
        elif is_bold:
            return f'<p style="{style}"><strong>{escaped_text}</strong></p>'
        else:
            return f'<p style="{style}">{escaped_text}</p>'
    
    def _detect_alignment(self, block: dict, page_width: float, page_center: float) -> str:
        """
        Détecte l'alignement d'un bloc de texte basé sur sa position.
        """
        bbox = block.get("bbox", [0, 0, page_width, 0])
        x0, y0, x1, y1 = bbox
        
        block_center = (x0 + x1) / 2
        block_width = x1 - x0
        
        # Marges typiques (environ 10% de chaque côté)
        left_margin = page_width * 0.1
        right_margin = page_width * 0.9
        
        # Vérifier si le bloc est centré
        if abs(block_center - page_center) < page_width * 0.05:
            # Le centre du bloc est proche du centre de la page
            if x0 > left_margin and x1 < right_margin:
                return "center"
        
        # Vérifier alignement à droite
        if x1 > right_margin - 10 and x0 > page_center:
            return "right"
        
        # Vérifier si justifié (bloc large qui touche les deux marges)
        if x0 < left_margin + 20 and x1 > right_margin - 20:
            return "justify"
        
        # Par défaut, aligné à gauche
        return "left"
    
    def _process_image_block(self, block: dict, page_num: int, img_output_dir: str, img_rel_path: str) -> str:
        """
        Traite un bloc image.
        """
        try:
            # Les images sont déjà extraites par pymupdf4llm
            # On pourrait ajouter une extraction manuelle ici si nécessaire
            return ""
        except Exception as e:
            logger.warning(f"Erreur traitement image: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """
        Nettoie le texte extrait.
        """
        if not text:
            return ""
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # Nettoyer les espaces multiples (mais garder les sauts de ligne)
        text = re.sub(r'[^\S\n]+', ' ', text)
        
        # Nettoyer les lignes vides multiples
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()


def get_ocr_service() -> OCRProvider:
    """Retourne le service OCR par défaut."""
    return PyMuPDF4LLMService()
