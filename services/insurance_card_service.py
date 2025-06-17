"""
Insurance Card Service - Advanced Tesseract Implementation
Optimized OCR service for German insurance cards using advanced Tesseract with EasyOCR-level preprocessing
"""
import pytesseract
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
import re
from PIL import Image
import io
import numpy as np
import cv2

logger = logging.getLogger(__name__)

class InsuranceCardService:
    """Service for processing German insurance cards with advanced Tesseract"""
    
    def __init__(self, db: Session):
        self.db = db
        logger.info("Advanced Tesseract OCR initialized for German insurance card processing")
    
    def extract_card_data(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract data from insurance card image using advanced Tesseract preprocessing
        Combines Tesseract reliability with EasyOCR-level preprocessing quality
        """
        try:
            logger.info(f"Starting advanced Tesseract processing, image size: {len(image_bytes)} bytes")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"PIL Image loaded: {image.size}, mode: {image.mode}")
            
            # Convert to OpenCV format for advanced preprocessing
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            logger.info(f"Converted to OpenCV format: {image_cv.shape}")
            
            # Try multiple advanced approaches
            extracted_data = self._multi_approach_advanced_tesseract(image_cv)
            
            if not extracted_data:
                logger.warning("No OCR data extracted from any advanced approach")
                return {
                    "success": False,
                    "error": "Kein Text erkannt - bitte Bildqualität verbessern und erneut scannen",
                    "data": {},
                    "confidence": 0.0
                }
            
            logger.info(f"Advanced Tesseract extraction successful, text length: {len(extracted_data.get('text', ''))}")
            
            # Parse German insurance card data with enhanced patterns
            parsed_data = self._parse_german_insurance_card_enhanced(extracted_data['text'])
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
            
            logger.info(f"Advanced Tesseract success: {list(parsed_data.keys())}")
            
            return {
                "success": True,
                "data": parsed_data,
                "confidence": extracted_data['confidence'],
                "raw_ocr": extracted_data['text']
            }
            
        except Exception as e:
            logger.error(f"Advanced Tesseract processing error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"OCR-Verarbeitung fehlgeschlagen: {str(e)[:100]} - bitte erneut versuchen",
                "data": {},
                "confidence": 0.0
            }
    
    def _multi_approach_advanced_tesseract(self, image_cv) -> Optional[Dict[str, Any]]:
        """Try multiple advanced preprocessing approaches with optimized Tesseract configs"""
        approaches = [
            # Approach 1: German-optimized high quality
            {
                'name': 'german_optimized',
                'preprocessing': self._preprocess_for_german_text,
                'config': r'--oem 1 --psm 6 -l deu+eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜßabcdefghijklmnopqrstuvwxyzäöüß0123456789 ./:,-',
                'weight': 1.5
            },
            # Approach 2: Numbers and IDs specialized
            {
                'name': 'numbers_specialized',
                'preprocessing': self._preprocess_for_numbers,
                'config': r'--oem 1 --psm 8 -l eng -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'weight': 1.3
            },
            # Approach 3: Company names and large text
            {
                'name': 'company_names',
                'preprocessing': self._preprocess_for_companies,
                'config': r'--oem 1 --psm 7 -l deu -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ ',
                'weight': 1.2
            },
            # Approach 4: Ultra high quality preprocessing
            {
                'name': 'ultra_quality',
                'preprocessing': self._preprocess_ultra_quality,
                'config': r'--oem 1 --psm 6 -l deu+eng -c preserve_interword_spaces=1',
                'weight': 1.4
            },
            # Approach 5: Mixed case handling
            {
                'name': 'mixed_case',
                'preprocessing': self._preprocess_mixed_case,
                'config': r'--oem 1 --psm 6 -l deu+eng',
                'weight': 1.1
            }
        ]
        
        best_result = None
        best_score = 0
        all_results = []
        
        for i, approach in enumerate(approaches):
            try:
                logger.info(f"Trying advanced approach {i+1}: {approach['name']}")
                processed_img = approach['preprocessing'](image_cv)
                
                # Run Tesseract with optimized config
                text = pytesseract.image_to_string(processed_img, config=approach['config'])
                
                if not text or len(text.strip()) < 3:
                    logger.warning(f"Approach {i+1} extracted minimal text")
                    continue
                
                logger.info(f"Approach {i+1} extracted: {text[:100]}...")
                
                # Calculate quality score with enhanced scoring
                score = self._calculate_enhanced_score(text, approach['weight'])
                
                text_data = {
                    'text': text,
                    'confidence': min(score / 100, 0.95),
                    'approach': approach['name']
                }
                all_results.append(text_data)
                
                if score > best_score:
                    best_score = score
                    best_result = text_data
                    logger.info(f"New best result from {approach['name']}, score: {score}")
                    
            except Exception as e:
                logger.warning(f"Advanced approach {i+1} failed: {e}")
                continue
        
        # Intelligent combination of results
        if len(all_results) > 1 and best_result:
            combined_text = self._intelligent_combine_results(all_results)
            if combined_text and len(combined_text) > len(best_result.get('text', '')):
                best_result = {
                    'text': combined_text,
                    'confidence': 0.9,
                    'approach': 'combined_advanced'
                }
                logger.info("Using combined advanced result")
        
        if best_result:
            logger.info(f"Final best result ({best_result.get('approach')}): {best_result['text'][:200]}")
        
        return best_result
    
    def _calculate_enhanced_score(self, text: str, base_weight: float) -> float:
        """Enhanced scoring system inspired by EasyOCR approach"""
        score = len(text.strip()) * base_weight * 0.1
        
        # German name patterns (highest priority)
        german_names = re.findall(r'[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+', text)
        if german_names:
            score += 80 * len(german_names)
            logger.info(f"Found German names: {german_names}")
        
        # Insurance numbers (critical)
        insurance_numbers = re.findall(r'[A-Z]?\d{9,10}', text)
        if insurance_numbers:
            score += 70 * len(insurance_numbers)
            logger.info(f"Found insurance numbers: {insurance_numbers}")
        
        # German insurance companies
        companies = ['AOK', 'TECHNIKER', 'TK', 'BARMER', 'DAK', 'KKH', 'HEK', 'BKK', 'IKK', 'BAYERN']
        for company in companies:
            if company in text.upper():
                score += 60
                logger.info(f"Found insurance company: {company}")
        
        # Date patterns
        dates = re.findall(r'\d{1,2}[\/\.\-]\d{2,4}', text)
        if dates:
            score += 30 * len(dates)
            logger.info(f"Found dates: {dates}")
        
        # German umlauts (strong indicator)
        umlauts = len(re.findall(r'[äöüÄÖÜß]', text))
        if umlauts > 0:
            score += umlauts * 4
            logger.info(f"Found {umlauts} German umlauts")
        
        # Card-specific keywords
        card_keywords = ['VERSICHERTENKARTE', 'KRANKENVERSICHERT', 'EUROPEAN', 'HEALTH', 'BUNDESREPUBLIK']
        for keyword in card_keywords:
            if keyword in text.upper():
                score += 25
                logger.info(f"Found card keyword: {keyword}")
        
        return score
    
    def _preprocess_for_german_text(self, image_cv) -> np.ndarray:
        """Specialized preprocessing for German text and names"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Optimal scaling for German text
        height, width = gray.shape
        scale_factor = 2.5
        resized = cv2.resize(gray, (int(width * scale_factor), int(height * scale_factor)), interpolation=cv2.INTER_CUBIC)
        
        # Advanced contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(resized)
        
        # Gentle denoising
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
        
        # Morphological operations for better character separation
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def _preprocess_for_numbers(self, image_cv) -> np.ndarray:
        """Specialized preprocessing for insurance numbers"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # High resolution for small numbers
        height, width = gray.shape
        resized = cv2.resize(gray, (width * 4, height * 4), interpolation=cv2.INTER_CUBIC)
        
        # High contrast for crisp numbers
        _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Clean up noise
        kernel = np.ones((1,1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        return cleaned
    
    def _preprocess_for_companies(self, image_cv) -> np.ndarray:
        """Specialized preprocessing for company names like AOK"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Medium scaling
        height, width = gray.shape
        resized = cv2.resize(gray, (width * 3, height * 3), interpolation=cv2.INTER_LANCZOS4)
        
        # Strong contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(resized)
        
        # Binary threshold
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
    
    def _preprocess_ultra_quality(self, image_cv) -> np.ndarray:
        """Ultra high quality preprocessing"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Very high resolution
        height, width = gray.shape
        resized = cv2.resize(gray, (width * 5, height * 5), interpolation=cv2.INTER_LANCZOS4)
        
        # Advanced denoising
        denoised = cv2.fastNlMeansDenoising(resized, None, 8, 7, 21)
        
        # Adaptive enhancement
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Sharpening
        kernel = np.array([[-1,-1,-1], [-1, 9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        return sharpened
    
    def _preprocess_mixed_case(self, image_cv) -> np.ndarray:
        """Preprocessing optimized for mixed case text"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Moderate scaling
        height, width = gray.shape
        resized = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
        
        # Balanced contrast
        clahe = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8,8))
        enhanced = clahe.apply(resized)
        
        return enhanced
    
    def _intelligent_combine_results(self, results: List[Dict]) -> str:
        """Intelligently combine multiple OCR results"""
        combined_data = {
            'names': [],
            'numbers': [],
            'companies': [],
            'dates': [],
            'other_lines': []
        }
        
        for result in results:
            text = result.get('text', '')
            if not text:
                continue
                
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            for line in lines:
                # Classify and store best examples
                if re.search(r'[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+', line):
                    combined_data['names'].append(line)
                elif re.search(r'\d{8,10}', line):
                    combined_data['numbers'].append(line)
                elif any(company in line.upper() for company in ['AOK', 'TK', 'BARMER', 'DAK', 'TECHNIKER']):
                    combined_data['companies'].append(line)
                elif re.search(r'\d{1,2}[\/\.\-]\d{2,4}', line):
                    combined_data['dates'].append(line)
                elif len(line) > 3:
                    combined_data['other_lines'].append(line)
        
        # Build optimal combination
        result_lines = []
        
        # Best name (longest and most complete)
        if combined_data['names']:
            best_name = max(combined_data['names'], key=lambda x: (len(x), x.count(' ')))
            result_lines.append(best_name)
        
        # Best company
        if combined_data['companies']:
            best_company = max(combined_data['companies'], key=len)
            result_lines.append(best_company)
        
        # All unique numbers
        unique_numbers = list(set(combined_data['numbers']))
        result_lines.extend(unique_numbers)
        
        # All dates
        unique_dates = list(set(combined_data['dates']))
        result_lines.extend(unique_dates)
        
        # Best additional lines
        result_lines.extend(combined_data['other_lines'][:2])
        
        return '\n'.join(result_lines)
    
    def _parse_german_insurance_card_enhanced(self, text: str) -> Dict[str, str]:
        """Enhanced German insurance card parsing with better patterns"""
        data = {
            'name': '',
            'insurance_number': '',
            'insurance_company': '',
            'birth_date': '',
            'valid_until': ''
        }
        
        if not text or not text.strip():
            logger.warning("Empty text provided to enhanced parser")
            return data
        
        lines = text.split('\n') if '\n' in text else [text]
        text_clean = ' '.join(lines).strip()
        
        # Enhanced name extraction with multiple patterns
        name_patterns = [
            r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,3})',  # Standard German names
            r'([A-ZÄÖÜ][A-ZÄÖÜ\s]+)',  # All caps names
            r'([A-Za-zÄÖÜäöüß\-]+\s+[A-Za-zÄÖÜäöüß\-]+)',  # Mixed case with hyphens
        ]
        
        for pattern in name_patterns:
            name_matches = re.findall(pattern, text_clean)
            for potential_name in name_matches:
                potential_name = potential_name.strip()
                # Enhanced validation
                if (len(potential_name.split()) >= 2 and 
                    not any(company in potential_name.upper() for company in ['AOK', 'TK', 'BARMER', 'DAK', 'TECHNIKER', 'KRANKENKASSE']) and
                    len(potential_name) <= 50 and
                    not re.search(r'\d', potential_name) and  # No digits in names
                    not potential_name.upper() in ['VERSICHERTENKARTE', 'EUROPEAN HEALTH']):
                    data['name'] = potential_name
                    break
            if data['name']:
                break
        
        # Enhanced insurance number patterns
        number_patterns = [
            r'([A-Z]\d{9})',     # Letter + 9 digits (most common)
            r'(\d{10})',         # 10 digits
            r'([A-Z]\d{8})',     # Letter + 8 digits (some variations)
        ]
        
        for pattern in number_patterns:
            number_match = re.search(pattern, text_clean)
            if number_match:
                data['insurance_number'] = number_match.group(1)
                break
        
        # Enhanced date extraction
        date_patterns = [
            r'(\d{1,2}[\/\.]\d{2,4})',     # MM/YY or MM/YYYY
            r'(\d{2}\.\d{2}\.\d{4})',      # DD.MM.YYYY
            r'(\d{1,2}\-\d{2,4})',         # MM-YY
        ]
        
        all_dates = []
        for pattern in date_patterns:
            dates = re.findall(pattern, text_clean)
            all_dates.extend(dates)
        
        if all_dates:
            # Smart date assignment
            data['valid_until'] = all_dates[-1]  # Usually the last date is validity
            if len(all_dates) > 1:
                data['birth_date'] = all_dates[0]
        
        # Comprehensive insurance company detection
        companies = [
            'AOK', 'TK', 'Techniker', 'TECHNIKER KRANKENKASSE',
            'Barmer', 'BARMER', 'DAK', 'DAK-GESUNDHEIT',
            'KKH', 'HEK', 'Pronova', 'BKK', 'IKK',
            'Knappschaft', 'SVLFG', 'BAYERN', 'SBK'
        ]
        
        text_upper = text_clean.upper()
        for company in companies:
            if company.upper() in text_upper:
                data['insurance_company'] = company
                break
        
        # Log successful extractions
        found_fields = [k for k, v in data.items() if v]
        logger.info(f"Enhanced parsing extracted: {found_fields}")
        
        return data
    
    def validate_card_type(self, image_bytes: bytes) -> Dict[str, Any]:
        """Simple card validation - assume it's an insurance card"""
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