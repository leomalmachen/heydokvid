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
            logger.info(f"Starting OCR processing, image size: {len(image_bytes)} bytes")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"PIL Image loaded: {image.size}, mode: {image.mode}")
            
            # Convert to OpenCV format for preprocessing
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            logger.info(f"Converted to OpenCV format: {image_cv.shape}")
            
            # Test basic pytesseract functionality first
            try:
                # Simple test
                gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
                simple_text = pytesseract.image_to_string(gray, config='--psm 6')
                logger.info(f"Basic OCR test successful, found text length: {len(simple_text)}")
                
                if simple_text.strip():
                    logger.info(f"Sample text: {simple_text[:100]}...")
                
            except Exception as e:
                logger.error(f"Basic pytesseract test failed: {e}")
                return {
                    "success": False,
                    "error": f"OCR-Engine nicht verfügbar: {str(e)[:100]}",
                    "data": {},
                    "confidence": 0.0
                }
            
            # Try multiple OCR approaches for better name recognition
            extracted_data = self._multi_approach_ocr(image_cv)
            
            if not extracted_data:
                logger.warning("No OCR data extracted from any approach")
                return {
                    "success": False,
                    "error": "Kein Text erkannt - bitte Bildqualität verbessern und erneut scannen",
                    "data": {},
                    "confidence": 0.0
                }
            
            logger.info(f"OCR extraction successful, text length: {len(extracted_data.get('text', ''))}")
            
            # Parse German insurance card data
            parsed_data = self._parse_german_insurance_card(extracted_data['text'])
            logger.info(f"Parsed data keys: {list(parsed_data.keys())}")
            
            # Check if we found meaningful data
            meaningful_data = any([
                parsed_data.get('name'),
                parsed_data.get('insurance_number'),
                parsed_data.get('insurance_company')
            ])
            
            if not meaningful_data:
                logger.warning(f"No meaningful data found, raw text: {extracted_data['text'][:200]}")
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
            logger.error(f"Pytesseract processing error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"OCR-Verarbeitung fehlgeschlagen: {str(e)[:100]} - bitte erneut versuchen",
                "data": {},
                "confidence": 0.0
            }
    
    def _multi_approach_ocr(self, image_cv) -> Optional[Dict[str, Any]]:
        """Try multiple OCR approaches and return the best result"""
        approaches = [
            # Approach 1: High-quality German OCR for names
            {
                'preprocessing': self._preprocess_for_text,
                'config': r'--oem 3 --psm 6 -l deu+eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜßabcdefghijklmnopqrstuvwxyzäöüß0123456789 ',
                'weight': 1.5
            },
            # Approach 2: Numbers and ID recognition
            {
                'preprocessing': self._preprocess_for_numbers,
                'config': r'--oem 3 --psm 8 -l eng -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'weight': 1.2
            },
            # Approach 3: Large text blocks (company names)
            {
                'preprocessing': self._preprocess_for_companies,
                'config': r'--oem 3 --psm 7 -l deu -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ ',
                'weight': 1.0
            },
            # Approach 4: High DPI with better segmentation
            {
                'preprocessing': self._preprocess_high_quality,
                'config': r'--oem 3 --psm 6 -l deu+eng',
                'weight': 1.3
            }
        ]
        
        best_result = None
        best_score = 0
        all_texts = []
        
        for i, approach in enumerate(approaches):
            try:
                processed_img = approach['preprocessing'](image_cv)
                text = pytesseract.image_to_string(processed_img, config=approach['config'])
                
                logger.info(f"Approach {i+1} result: {text[:100] if text else 'No text'}...")
                
                if text and len(text.strip()) > 3:
                    # Advanced scoring based on expected patterns
                    score = self._calculate_ocr_score(text, approach['weight'])
                    
                    all_texts.append(text)
                    
                    if score > best_score:
                        best_score = score
                        best_result = {
                            'text': text,
                            'confidence': min(score / 100, 0.95),
                            'approach': i+1
                        }
                        logger.info(f"New best result from approach {i+1}, score: {score}")
                        
            except Exception as e:
                logger.warning(f"OCR approach {i+1} failed: {e}")
                continue
        
        # If we have multiple texts, try to combine them intelligently
        if len(all_texts) > 1 and best_result:
            combined_text = self._intelligent_combine_ocr_results(all_texts)
            best_text_length = len(best_result.get('text', ''))
            if combined_text and len(combined_text) > best_text_length:
                best_result = {
                    'text': combined_text,
                    'confidence': 0.9,
                    'approach': 'combined'
                }
                logger.info("Using combined OCR result")
        
        if best_result:
            logger.info(f"Final best result (approach {best_result.get('approach')}): {best_result['text'][:200]}")
        
        return best_result

    def _calculate_ocr_score(self, text: str, base_weight: float) -> float:
        """Calculate OCR quality score based on expected patterns"""
        score = len(text.strip()) * base_weight
        
        # German name patterns (very important)
        german_names = re.findall(r'[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+', text)
        if german_names:
            score += 50 * len(german_names)
            logger.info(f"Found German names: {german_names}")
        
        # Insurance numbers (10 digits, sometimes with letter)
        insurance_numbers = re.findall(r'[A-Z]?\d{9,10}', text)
        if insurance_numbers:
            score += 40 * len(insurance_numbers)
            logger.info(f"Found insurance numbers: {insurance_numbers}")
        
        # German insurance companies
        companies = ['AOK', 'TECHNIKER', 'TK', 'BARMER', 'DAK', 'KKH', 'HEK', 'BKK', 'IKK', 'BAYERN']
        for company in companies:
            if company in text.upper():
                score += 30
                logger.info(f"Found insurance company: {company}")
        
        # Date patterns
        dates = re.findall(r'\d{1,2}[\/\.]\d{2,4}', text)
        if dates:
            score += 15 * len(dates)
        
        return score

    def _preprocess_for_text(self, image_cv) -> np.ndarray:
        """Enhanced preprocessing for German text/names"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Resize image for better OCR (make it bigger)
        height, width = gray.shape
        scale_factor = 3.0
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        resized = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(resized, (3, 3), 0)
        
        # Enhanced adaptive threshold
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
        )
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def _preprocess_for_numbers(self, image_cv) -> np.ndarray:
        """Aggressive preprocessing optimized for numbers"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Resize for better number recognition
        height, width = gray.shape
        resized = cv2.resize(gray, (width * 4, height * 4), interpolation=cv2.INTER_CUBIC)
        
        # Sharpen the image
        kernel = np.array([[-1,-1,-1,-1,-1],
                          [-1, 2, 2, 2,-1],
                          [-1, 2, 8, 2,-1],
                          [-1, 2, 2, 2,-1],
                          [-1,-1,-1,-1,-1]]) / 8.0
        sharpened = cv2.filter2D(resized, -1, kernel)
        
        # High contrast threshold
        _, thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Remove small noise
        kernel = np.ones((2,2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        return cleaned

    def _preprocess_for_companies(self, image_cv) -> np.ndarray:
        """Preprocessing for company names (AOK, etc.)"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Resize
        height, width = gray.shape
        resized = cv2.resize(gray, (width * 3, height * 3), interpolation=cv2.INTER_LANCZOS4)
        
        # Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(resized)
        
        # Threshold
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh

    def _preprocess_high_quality(self, image_cv) -> np.ndarray:
        """High-quality preprocessing with multiple steps"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Large upscale for very high quality
        height, width = gray.shape
        resized = cv2.resize(gray, (width * 5, height * 5), interpolation=cv2.INTER_LANCZOS4)
        
        # Noise reduction
        denoised = cv2.fastNlMeansDenoising(resized)
        
        # Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Adaptive threshold with larger block
        thresh = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
        )
        
        return thresh
    
    def _minimal_preprocess(self, image_cv) -> np.ndarray:
        """Minimal preprocessing - just grayscale and resize"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        return cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
    
    def _intelligent_combine_ocr_results(self, texts) -> str:
        """Intelligently combine OCR results by extracting best parts"""
        combined_data = {
            'names': [],
            'numbers': [],
            'companies': [],
            'other_lines': []
        }
        
        for text in texts:
            if not text:
                continue
                
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            for line in lines:
                # Classify each line
                if re.search(r'[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+', line):
                    combined_data['names'].append(line)
                elif re.search(r'\d{8,10}', line):
                    combined_data['numbers'].append(line)
                elif any(company in line.upper() for company in ['AOK', 'TK', 'BARMER', 'DAK']):
                    combined_data['companies'].append(line)
                else:
                    combined_data['other_lines'].append(line)
        
        # Build best combination
        result_lines = []
        
        # Best name (longest valid name)
        if combined_data['names']:
            best_name = max(combined_data['names'], key=len)
            result_lines.append(best_name)
        
        # Best company
        if combined_data['companies']:
            best_company = max(combined_data['companies'], key=len)
            result_lines.append(best_company)
        
        # All unique numbers
        unique_numbers = list(set(combined_data['numbers']))
        result_lines.extend(unique_numbers)
        
        # Other important lines
        result_lines.extend(combined_data['other_lines'][:3])  # Max 3 additional lines
        
        return '\n'.join(result_lines)
    
    def _parse_german_insurance_card(self, text: str) -> Dict[str, str]:
        """Parse German insurance card text - simple extraction"""
        data = {
            'name': '',
            'insurance_number': '',
            'insurance_company': '',
            'birth_date': '',
            'valid_until': ''
        }
        
        # Add null/empty check
        if not text or not text.strip():
            logger.warning("Empty text provided to parser")
            return data
        
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