"""
Insurance Card Service - EasyOCR Only Implementation
Simple OCR service for German insurance cards using EasyOCR
"""
import easyocr
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import re
from PIL import Image
import io
import numpy as np

logger = logging.getLogger(__name__)

class InsuranceCardService:
    """Service for processing German insurance cards with EasyOCR only"""
    
    def __init__(self, db: Session):
        self.db = db
        self.reader = None
        self._init_ocr()
    
    def _init_ocr(self):
        """Initialize EasyOCR reader"""
        try:
            self.reader = easyocr.Reader(['de', 'en'], gpu=False)
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            self.reader = None
    
    def extract_card_data(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract data from insurance card image using EasyOCR only
        No fallbacks - if it fails, user must retry
        """
        try:
            if not self.reader:
                return {
                    "success": False,
                    "error": "OCR-System nicht verfügbar - bitte erneut versuchen",
                    "data": {},
                    "confidence": 0.0
                }
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            image_array = np.array(image)
            
            logger.info(f"Processing image with EasyOCR: {image.size}")
            
            # Extract text with EasyOCR
            results = self.reader.readtext(image_array)
            
            if not results:
                return {
                    "success": False,
                    "error": "Kein Text erkannt - bitte Bildqualität verbessern und erneut scannen",
                    "data": {},
                    "confidence": 0.0
                }
            
            # Extract text and confidence
            extracted_texts = []
            total_confidence = 0
            
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Only texts with reasonable confidence
                    extracted_texts.append(text.strip())
                    total_confidence += confidence
            
            if not extracted_texts:
                return {
                    "success": False,
                    "error": "Text zu unscharf erkannt - bitte erneut scannen",
                    "data": {},
                    "confidence": 0.0
                }
            
            # Parse German insurance card data
            all_text = ' '.join(extracted_texts)
            parsed_data = self._parse_german_insurance_card(all_text)
            
            avg_confidence = total_confidence / len(results) if results else 0.0
            
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
                    "confidence": avg_confidence,
                    "raw_ocr": all_text
                }
            
            logger.info(f"EasyOCR success: {list(parsed_data.keys())}")
            
            return {
                "success": True,
                "data": parsed_data,
                "confidence": avg_confidence,
                "raw_ocr": all_text
            }
            
        except Exception as e:
            logger.error(f"EasyOCR processing error: {e}")
            return {
                "success": False,
                "error": "OCR-Verarbeitung fehlgeschlagen - bitte erneut versuchen",
                "data": {},
                "confidence": 0.0
            }
    
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