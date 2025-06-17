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
            
            logger.info(f"Processing image with pytesseract: {image.size}")
            
            # Try multiple OCR approaches for better name recognition
            extracted_data = self._multi_approach_ocr(image_cv)
            
            if not extracted_data:
                return {
                    "success": False,
                    "error": "Kein Text erkannt - bitte Bildqualität verbessern und erneut scannen",
                    "data": {},
                    "confidence": 0.0
                }
            
            # Parse German insurance card data
            parsed_data = self._parse_german_insurance_card(extracted_data['text'])
            
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
                    "raw_ocr": extracted_data['text']
                }
            
            logger.info(f"Pytesseract success: {list(parsed_data.keys())}")
            
            return {
                "success": True,
                "data": parsed_data,
                "confidence": extracted_data['confidence'],
                "raw_ocr": extracted_data['text']
            }
            
        except Exception as e:
            logger.error(f"Pytesseract processing error: {e}")
            return {
                "success": False,
                "error": "OCR-Verarbeitung fehlgeschlagen - bitte erneut versuchen",
                "data": {},
                "confidence": 0.0
            }
    
    def _multi_approach_ocr(self, image_cv):
        """Try multiple OCR approaches and return the best result"""
        approaches = [
            # Approach 1: Gentle preprocessing for names
            {
                'preprocessing': self._preprocess_for_text,
                'config': r'--oem 3 --psm 6 -l deu',
                'weight': 1.0
            },
            # Approach 2: High contrast for numbers  
            {
                'preprocessing': self._preprocess_for_numbers,
                'config': r'--oem 3 --psm 7 -l deu',
                'weight': 0.8
            },
            # Approach 3: Original image with minimal processing
            {
                'preprocessing': self._minimal_preprocess,
                'config': r'--oem 3 --psm 6 -l deu+eng',
                'weight': 0.9
            }
        ]
        
        best_result = None
        best_score = 0
        all_texts = []
        
        for approach in approaches:
            try:
                processed_img = approach['preprocessing'](image_cv)
                text = pytesseract.image_to_string(processed_img, config=approach['config'])
                
                if text and len(text.strip()) > 5:
                    # Simple scoring based on text length and expected patterns
                    score = len(text.strip()) * approach['weight']
                    
                    # Bonus for finding name patterns
                    if re.search(r'[A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+', text):
                        score += 20
                    
                    # Bonus for finding insurance numbers
                    if re.search(r'[A-Z]?\d{8,10}', text):
                        score += 15
                        
                    all_texts.append(text)
                    
                    if score > best_score:
                        best_score = score
                        best_result = {
                            'text': text,
                            'confidence': min(score / 100, 0.95)
                        }
                        
            except Exception as e:
                logger.warning(f"OCR approach failed: {e}")
                continue
        
        # If we have multiple texts, try to combine them
        if len(all_texts) > 1:
            combined_text = self._combine_ocr_results(all_texts)
            if combined_text and len(combined_text) > (best_result['text'] if best_result else ''):
                best_result = {
                    'text': combined_text,
                    'confidence': 0.85
                }
        
        return best_result
    
    def _preprocess_for_text(self, image_cv):
        """Gentle preprocessing optimized for text/names"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Very gentle blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (1, 1), 0)
        
        # Adaptive threshold with larger block size for text
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 4
        )
        
        return thresh
    
    def _preprocess_for_numbers(self, image_cv):
        """More aggressive preprocessing for numbers"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Sharpen for numbers
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        
        # High contrast threshold
        _, thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
    
    def _minimal_preprocess(self, image_cv):
        """Minimal preprocessing - just grayscale"""
        return cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    
    def _combine_ocr_results(self, texts):
        """Combine multiple OCR results to get the best parts"""
        combined_lines = []
        
        for text in texts:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            combined_lines.extend(lines)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_lines = []
        for line in combined_lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
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