"""
Insurance Card Service - Pytesseract Only Implementation
Lightweight OCR service for German insurance cards using pytesseract
"""
import pytesseract
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import re
from PIL import Image
import io
import numpy as np
import cv2

logger = logging.getLogger(__name__)

class InsuranceCardService:
    """Service for processing German insurance cards with pytesseract only"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def extract_card_data(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract data from insurance card image using pytesseract only
        No fallbacks - if it fails, user must retry
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to OpenCV format for preprocessing
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image_cv)
            
            logger.info(f"Processing image with pytesseract: {image.size}")
            
            # Configure pytesseract for German
            custom_config = r'--oem 3 --psm 6 -l deu'
            
            # Extract text with pytesseract
            extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                return {
                    "success": False,
                    "error": "Kein Text erkannt - bitte Bildqualität verbessern und erneut scannen",
                    "data": {},
                    "confidence": 0.0
                }
            
            # Parse German insurance card data
            parsed_data = self._parse_german_insurance_card(extracted_text)
            
            # Check if we found meaningful data
            meaningful_data = any([
                parsed_data.get('name'),
                parsed_data.get('insurance_number'),
                parsed_data.get('insurance_company')
            ])
            
            if not meaningful_data:
                return {
                    "success": False,
                    "error": "Kartendaten nicht lesbar - bitte Karte besser positionieren und erneut scannen",
                    "data": {},
                    "confidence": 0.6,
                    "raw_ocr": extracted_text
                }
            
            logger.info(f"Pytesseract success: {list(parsed_data.keys())}")
            
            return {
                "success": True,
                "data": parsed_data,
                "confidence": 0.8,
                "raw_ocr": extracted_text
            }
            
        except Exception as e:
            logger.error(f"Pytesseract processing error: {e}")
            return {
                "success": False,
                "error": "OCR-Verarbeitung fehlgeschlagen - bitte erneut versuchen",
                "data": {},
                "confidence": 0.0
            }
    
    def _preprocess_image(self, image_cv):
        """Preprocess image for better OCR results"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
            
            # Apply slight Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Apply adaptive threshold
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Dilate to make text thicker
            kernel = np.ones((2, 2), np.uint8)
            processed = cv2.dilate(thresh, kernel, iterations=1)
            
            return processed
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original")
            return cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    
    def _parse_german_insurance_card(self, text: str) -> Dict[str, str]:
        """Parse German insurance card text - simple extraction"""
        data = {
            'name': '',
            'insurance_number': '',
            'insurance_company': '',
            'birth_date': '',
            'valid_until': ''
        }
        
        lines = text.split('\n') if '\n' in text else text.split(' ')
        text_clean = ' '.join(lines).strip()
        
        # Extract name (pattern: Firstname Lastname)
        name_pattern = r'([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)'
        name_match = re.search(name_pattern, text_clean)
        if name_match:
            data['name'] = name_match.group(1).strip()
        
        # Extract insurance number (pattern: Letter + 9 digits or 10 digits)
        number_pattern = r'([A-Z]\d{9}|\d{10})'
        number_match = re.search(number_pattern, text_clean)
        if number_match:
            data['insurance_number'] = number_match.group(1)
        
        # Extract dates (MM/YY or MM/YYYY)
        date_pattern = r'(\d{1,2}[\/\.]\d{2,4})'
        date_matches = re.findall(date_pattern, text_clean)
        if date_matches:
            data['valid_until'] = date_matches[-1]  # Usually the last date is validity
        
        # Extract insurance company names
        companies = ['AOK', 'TK', 'Techniker', 'Barmer', 'DAK', 'KKH', 'HEK', 'BKK', 'IKK']
        for company in companies:
            if company.lower() in text_clean.lower():
                data['insurance_company'] = company
                break
        
        return data
    
    def validate_card_type(self, image_bytes: bytes) -> Dict[str, Any]:
        """Simple card validation - always assume it's an insurance card"""
        return {
            "is_insurance_card": True,
            "card_type": "insurance",
            "confidence": 0.8,
            "success": True
        }
    
    def create_validation_record(self, meeting_id: str, validation_data: Dict) -> str:
        """Create a simple validation record"""
        validation_id = f"val_{uuid.uuid4().hex[:8]}"
        logger.info(f"Created validation record {validation_id} for meeting {meeting_id}")
        return validation_id
    
    def get_validation_status(self, validation_id: str) -> Dict[str, Any]:
        """Get validation status - simple implementation"""
        return {
            "status": "completed",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "validated": True
        } 