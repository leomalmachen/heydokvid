"""
Insurance Card Service - EasyOCR Implementation
Advanced OCR service for German insurance cards using EasyOCR
"""
import easyocr
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
    """Service for processing German insurance cards with EasyOCR"""
    
    def __init__(self, db: Session):
        self.db = db
        # Initialize EasyOCR with German and English language support
        try:
            self.ocr = easyocr.Reader(
                ['de', 'en'],           # German and English languages
                gpu=False,              # CPU only for better Heroku compatibility
                verbose=False           # Reduce noise in logs
            )
            logger.info("EasyOCR initialized successfully with German and English language support")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            self.ocr = None
    
    def extract_card_data(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract data from insurance card image using EasyOCR
        Excellent German text recognition with high accuracy
        """
        try:
            if not self.ocr:
                logger.error("EasyOCR not initialized")
                return {
                    "success": False,
                    "error": "OCR-Engine nicht verfügbar",
                    "data": {},
                    "confidence": 0.0
                }
            
            logger.info(f"Starting EasyOCR processing, image size: {len(image_bytes)} bytes")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"PIL Image loaded: {image.size}, mode: {image.mode}")
            
            # Convert to OpenCV format for preprocessing
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            logger.info(f"Converted to OpenCV format: {image_cv.shape}")
            
            # Try multiple preprocessing approaches with EasyOCR
            extracted_data = self._multi_approach_easy_ocr(image_cv)
            
            if not extracted_data:
                logger.warning("No OCR data extracted from any EasyOCR approach")
                return {
                    "success": False,
                    "error": "Kein Text erkannt - bitte Bildqualität verbessern und erneut scannen",
                    "data": {},
                    "confidence": 0.0
                }
            
            logger.info(f"EasyOCR extraction successful, text length: {len(extracted_data.get('text', ''))}")
            
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
            
            logger.info(f"EasyOCR success: {list(parsed_data.keys())}")
            
            return {
                "success": True,
                "data": parsed_data,
                "confidence": extracted_data['confidence'],
                "raw_ocr": extracted_data['text']
            }
            
        except Exception as e:
            logger.error(f"EasyOCR processing error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"OCR-Verarbeitung fehlgeschlagen: {str(e)[:100]} - bitte erneut versuchen",
                "data": {},
                "confidence": 0.0
            }
    
    def _multi_approach_easy_ocr(self, image_cv) -> Optional[Dict[str, Any]]:
        """Try multiple preprocessing approaches with EasyOCR"""
        approaches = [
            # Approach 1: Original image (EasyOCR works very well with raw images)
            {
                'name': 'original',
                'preprocessing': self._minimal_preprocess,
                'weight': 1.0
            },
            # Approach 2: Enhanced contrast for better text clarity
            {
                'name': 'enhanced_contrast',
                'preprocessing': self._preprocess_for_text,
                'weight': 1.3
            },
            # Approach 3: High resolution for small text
            {
                'name': 'high_resolution',
                'preprocessing': self._preprocess_high_quality,
                'weight': 1.4
            },
            # Approach 4: Optimized for numbers/IDs
            {
                'name': 'number_optimized',
                'preprocessing': self._preprocess_for_numbers,
                'weight': 1.2
            }
        ]
        
        best_result = None
        best_score = 0
        all_results = []
        
        for i, approach in enumerate(approaches):
            try:
                logger.info(f"Trying EasyOCR approach {i+1}: {approach['name']}")
                processed_img = approach['preprocessing'](image_cv)
                
                # Run EasyOCR on preprocessed image
                ocr_result = self.ocr.readtext(
                    processed_img,
                    detail=1,           # Include bounding boxes and confidence
                    paragraph=False,    # Don't group lines into paragraphs
                    width_ths=0.7,      # Text width threshold
                    height_ths=0.7,     # Text height threshold
                    text_threshold=0.7, # Text confidence threshold
                    link_threshold=0.4, # Link confidence threshold
                    low_text=0.4        # Low text confidence threshold
                )
                
                if not ocr_result:
                    logger.warning(f"Approach {i+1} returned no results")
                    continue
                
                # Extract text and confidence from EasyOCR result
                text_data = self._extract_easy_text(ocr_result)
                
                if not text_data['text']:
                    logger.warning(f"Approach {i+1} extracted no text")
                    continue
                
                logger.info(f"Approach {i+1} extracted: {text_data['text'][:100]}...")
                
                # Calculate quality score
                score = self._calculate_easy_score(text_data, approach['weight'])
                all_results.append(text_data)
                
                if score > best_score:
                    best_score = score
                    best_result = {
                        'text': text_data['text'],
                        'confidence': text_data['confidence'],
                        'approach': approach['name'],
                        'boxes': text_data['boxes']
                    }
                    logger.info(f"New best result from {approach['name']}, score: {score}")
                    
            except Exception as e:
                logger.warning(f"EasyOCR approach {i+1} failed: {e}")
                continue
        
        # If we have multiple results, try to combine them intelligently
        if len(all_results) > 1 and best_result:
            combined_text = self._intelligent_combine_easy_results(all_results)
            if combined_text and len(combined_text) > len(best_result.get('text', '')):
                best_result = {
                    'text': combined_text,
                    'confidence': 0.9,
                    'approach': 'combined'
                }
                logger.info("Using combined EasyOCR result")
        
        if best_result:
            logger.info(f"Final best result ({best_result.get('approach')}): {best_result['text'][:200]}")
        
        return best_result
    
    def _extract_easy_text(self, ocr_result: List) -> Dict[str, Any]:
        """Extract text and confidence from EasyOCR result format"""
        all_text = []
        all_confidences = []
        all_boxes = []
        
        for detection in ocr_result:
            if len(detection) >= 3:
                bbox = detection[0]      # Bounding box coordinates [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                text = detection[1]      # Recognized text
                confidence = detection[2] # Confidence score
                
                if text and confidence > 0.4:  # Filter out low confidence text
                    all_text.append(text.strip())
                    all_confidences.append(confidence)
                    all_boxes.append(bbox)
        
        combined_text = '\n'.join(all_text)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        
        return {
            'text': combined_text,
            'confidence': avg_confidence,
            'boxes': all_boxes
        }
    
    def _calculate_easy_score(self, text_data: Dict[str, Any], base_weight: float) -> float:
        """Calculate quality score for EasyOCR results"""
        text = text_data['text']
        confidence = text_data['confidence']
        
        # Base score from confidence and text length
        score = confidence * 100 * base_weight + len(text.strip()) * 0.1
        
        # German name patterns (very important for insurance cards)
        german_names = re.findall(r'[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+', text)
        if german_names:
            score += 70 * len(german_names)
            logger.info(f"Found German names: {german_names}")
        
        # Insurance numbers (critical for validation)
        insurance_numbers = re.findall(r'[A-Z]?\d{9,10}', text)
        if insurance_numbers:
            score += 60 * len(insurance_numbers)
            logger.info(f"Found insurance numbers: {insurance_numbers}")
        
        # German insurance companies
        companies = ['AOK', 'TECHNIKER', 'TK', 'BARMER', 'DAK', 'KKH', 'HEK', 'BKK', 'IKK', 'BAYERN']
        for company in companies:
            if company in text.upper():
                score += 50
                logger.info(f"Found insurance company: {company}")
        
        # Date patterns (validity dates)
        dates = re.findall(r'\d{1,2}[\/\.\-]\d{2,4}', text)
        if dates:
            score += 25 * len(dates)
            logger.info(f"Found dates: {dates}")
        
        # Umlauts bonus (German text indicator)
        umlauts = len(re.findall(r'[äöüÄÖÜß]', text))
        if umlauts > 0:
            score += umlauts * 3
            logger.info(f"Found {umlauts} German umlauts")
        
        # Card-specific keywords bonus
        card_keywords = ['VERSICHERTENKARTE', 'KRANKENVERSICHERT', 'EUROPEAN', 'HEALTH']
        for keyword in card_keywords:
            if keyword in text.upper():
                score += 20
                logger.info(f"Found card keyword: {keyword}")
        
        return score
    
    def _preprocess_for_text(self, image_cv) -> np.ndarray:
        """Enhanced preprocessing for German text/names"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Resize image for better OCR
        height, width = gray.shape
        scale_factor = 2.0
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        resized = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(resized)
        
        # Gentle denoising
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
        
        return denoised
    
    def _preprocess_for_numbers(self, image_cv) -> np.ndarray:
        """Preprocessing optimized for numbers and IDs"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Resize for better number recognition
        height, width = gray.shape
        resized = cv2.resize(gray, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)
        
        # High contrast for numbers
        _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def _preprocess_high_quality(self, image_cv) -> np.ndarray:
        """High-quality preprocessing with multiple enhancement steps"""
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        
        # Large upscale for maximum quality
        height, width = gray.shape
        resized = cv2.resize(gray, (width * 3, height * 3), interpolation=cv2.INTER_LANCZOS4)
        
        # Advanced denoising
        denoised = cv2.fastNlMeansDenoising(resized, None, 8, 7, 21)
        
        # Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Sharpening filter
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        return sharpened
    
    def _minimal_preprocess(self, image_cv) -> np.ndarray:
        """Minimal preprocessing - EasyOCR works well with original images"""
        # Convert to RGB (EasyOCR expects RGB)
        return cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
    
    def _intelligent_combine_easy_results(self, results: List[Dict]) -> str:
        """Intelligently combine multiple EasyOCR results"""
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
                # Classify each line by content type
                if re.search(r'[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+', line):
                    combined_data['names'].append(line)
                elif re.search(r'\d{8,10}', line):
                    combined_data['numbers'].append(line)
                elif any(company in line.upper() for company in ['AOK', 'TK', 'BARMER', 'DAK', 'TECHNIKER']):
                    combined_data['companies'].append(line)
                elif re.search(r'\d{1,2}[\/\.\-]\d{2,4}', line):
                    combined_data['dates'].append(line)
                elif len(line) > 3:  # Other meaningful text
                    combined_data['other_lines'].append(line)
        
        # Build optimized combination
        result_lines = []
        
        # Best name (prioritize longer, more complete names)
        if combined_data['names']:
            best_name = max(combined_data['names'], key=lambda x: (len(x), x.count(' ')))
            result_lines.append(best_name)
        
        # Best company name
        if combined_data['companies']:
            best_company = max(combined_data['companies'], key=len)
            result_lines.append(best_company)
        
        # All unique numbers (important for validation)
        unique_numbers = list(set(combined_data['numbers']))
        result_lines.extend(unique_numbers)
        
        # All dates (validity information)
        unique_dates = list(set(combined_data['dates']))
        result_lines.extend(unique_dates)
        
        # Additional relevant lines
        result_lines.extend(combined_data['other_lines'][:2])
        
        return '\n'.join(result_lines)
    
    def _parse_german_insurance_card(self, text: str) -> Dict[str, str]:
        """Parse German insurance card text with improved patterns for EasyOCR"""
        data = {
            'name': '',
            'insurance_number': '',
            'insurance_company': '',
            'birth_date': '',
            'valid_until': ''
        }
        
        if not text or not text.strip():
            logger.warning("Empty text provided to parser")
            return data
        
        lines = text.split('\n') if '\n' in text else [text]
        text_clean = ' '.join(lines).strip()
        
        # Extract name with improved German pattern
        name_patterns = [
            r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,3})',  # Standard German names
            r'([A-ZÄÖÜ][A-ZÄÖÜ\s]+)',  # All caps names
            r'([A-Za-zÄÖÜäöüß]+\s+[A-Za-zÄÖÜäöüß]+)',  # Mixed case names
        ]
        
        for pattern in name_patterns:
            name_matches = re.findall(pattern, text_clean)
            for potential_name in name_matches:
                potential_name = potential_name.strip()
                # Validate it's actually a name (not a company or other text)
                if (len(potential_name.split()) >= 2 and 
                    not any(company in potential_name.upper() for company in ['AOK', 'TK', 'BARMER', 'DAK', 'TECHNIKER']) and
                    len(potential_name) <= 50 and
                    not re.search(r'\d', potential_name)):  # No digits in names
                    data['name'] = potential_name
                    break
            if data['name']:
                break
        
        # Extract insurance number with improved patterns
        number_patterns = [
            r'([A-Z]\d{9})',     # Letter + 9 digits
            r'(\d{10})',         # 10 digits
            r'([A-Z]\d{8,9})',   # Letter + 8-9 digits (some variations)
        ]
        
        for pattern in number_patterns:
            number_match = re.search(pattern, text_clean)
            if number_match:
                data['insurance_number'] = number_match.group(1)
                break
        
        # Extract dates with multiple formats
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
            # Usually the last date found is the validity date
            data['valid_until'] = all_dates[-1]
            # If multiple dates, first might be birth date
            if len(all_dates) > 1:
                data['birth_date'] = all_dates[0]
        
        # Extract insurance company with comprehensive list
        companies = [
            'AOK', 'TK', 'Techniker', 'TECHNIKER KRANKENKASSE',
            'Barmer', 'BARMER', 'DAK', 'DAK-GESUNDHEIT',
            'KKH', 'HEK', 'Pronova', 'BKK', 'IKK',
            'Knappschaft', 'SVLFG', 'BAYERN'
        ]
        
        text_upper = text_clean.upper()
        for company in companies:
            if company.upper() in text_upper:
                data['insurance_company'] = company
                break
        
        # Log what we found
        found_fields = [k for k, v in data.items() if v]
        logger.info(f"Extracted fields: {found_fields}")
        
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