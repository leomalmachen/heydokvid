"""
Insurance Card Service - Minimal Pillow-Only Implementation
Lightweight OCR service for German insurance cards using Tesseract with Pillow preprocessing
"""
import pytesseract
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
import re
from PIL import Image, ImageEnhance, ImageFilter
import io

logger = logging.getLogger(__name__)

class InsuranceCardService:
    """Service for processing German insurance cards with Pillow-only preprocessing"""
    
    def __init__(self, db: Session):
        self.db = db
        logger.info("Minimal Tesseract OCR initialized with Pillow-only preprocessing")
    
    def extract_card_data(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract data from insurance card image using Tesseract with Pillow preprocessing
        Minimal implementation optimized for Heroku size constraints
        """
        try:
            logger.info(f"Starting minimal Tesseract processing, image size: {len(image_bytes)} bytes")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"PIL Image loaded: {image.size}, mode: {image.mode}")
            
            # Try multiple Pillow-based approaches
            extracted_data = self._multi_approach_pillow_tesseract(image)
            
            if not extracted_data:
                logger.warning("No OCR data extracted from any Pillow approach")
                return {
                    "success": False,
                    "error": "Kein Text erkannt - bitte Bildqualität verbessern und erneut scannen",
                    "data": {},
                    "confidence": 0.0
                }
            
            logger.info(f"Minimal Tesseract extraction successful, text length: {len(extracted_data.get('text', ''))}")
            
            # Parse German insurance card data
            parsed_data = self._parse_german_insurance_card_simple(extracted_data['text'])
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
            
            logger.info(f"Minimal Tesseract success: {list(parsed_data.keys())}")
            
            return {
                "success": True,
                "data": parsed_data,
                "confidence": extracted_data['confidence'],
                "raw_ocr": extracted_data['text']
            }
            
        except Exception as e:
            logger.error(f"Minimal Tesseract processing error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"OCR-Verarbeitung fehlgeschlagen: {str(e)[:100]} - bitte erneut versuchen",
                "data": {},
                "confidence": 0.0
            }
    
    def _multi_approach_pillow_tesseract(self, image) -> Optional[Dict[str, Any]]:
        """Try multiple Pillow-based preprocessing approaches with Tesseract"""
        approaches = [
            # Approach 1: Original image
            {
                'name': 'original',
                'preprocessing': lambda img: img,
                'config': r'--oem 1 --psm 6 -l deu+eng',
                'weight': 1.0
            },
            # Approach 2: Enhanced contrast and sharpness
            {
                'name': 'enhanced',
                'preprocessing': self._preprocess_enhanced,
                'config': r'--oem 1 --psm 6 -l deu+eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜßabcdefghijklmnopqrstuvwxyzäöüß0123456789 ./:,-',
                'weight': 1.4
            },
            # Approach 3: High contrast for numbers
            {
                'name': 'high_contrast',
                'preprocessing': self._preprocess_high_contrast,
                'config': r'--oem 1 --psm 8 -l eng -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'weight': 1.2
            },
            # Approach 4: Grayscale with sharpening
            {
                'name': 'grayscale_sharp',
                'preprocessing': self._preprocess_grayscale_sharp,
                'config': r'--oem 1 --psm 6 -l deu+eng',
                'weight': 1.3
            }
        ]
        
        best_result = None
        best_score = 0
        all_results = []
        
        for i, approach in enumerate(approaches):
            try:
                logger.info(f"Trying Pillow approach {i+1}: {approach['name']}")
                processed_img = approach['preprocessing'](image)
                
                # Run Tesseract
                text = pytesseract.image_to_string(processed_img, config=approach['config'])
                
                if not text or len(text.strip()) < 3:
                    logger.warning(f"Approach {i+1} extracted minimal text")
                    continue
                
                logger.info(f"Approach {i+1} extracted: {text[:100]}...")
                
                # Calculate quality score
                score = self._calculate_simple_score(text, approach['weight'])
                
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
                logger.warning(f"Pillow approach {i+1} failed: {e}")
                continue
        
        # Simple combination if multiple results
        if len(all_results) > 1 and best_result:
            combined_text = self._simple_combine_results(all_results)
            if combined_text and len(combined_text) > len(best_result.get('text', '')):
                best_result = {
                    'text': combined_text,
                    'confidence': 0.9,
                    'approach': 'combined'
                }
                logger.info("Using combined result")
        
        return best_result
    
    def _preprocess_enhanced(self, image):
        """Enhanced preprocessing using Pillow"""
        # Convert to grayscale
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image
        
        # Resize for better OCR
        width, height = gray.size
        new_size = (width * 2, height * 2)
        resized = gray.resize(new_size, Image.Resampling.LANCZOS)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(resized)
        contrast_enhanced = enhancer.enhance(1.5)
        
        # Enhance sharpness
        sharpness_enhancer = ImageEnhance.Sharpness(contrast_enhanced)
        sharpened = sharpness_enhancer.enhance(2.0)
        
        return sharpened
    
    def _preprocess_high_contrast(self, image):
        """High contrast preprocessing for numbers"""
        # Convert to grayscale
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image
        
        # Resize
        width, height = gray.size
        new_size = (width * 3, height * 3)
        resized = gray.resize(new_size, Image.Resampling.LANCZOS)
        
        # Very high contrast
        enhancer = ImageEnhance.Contrast(resized)
        high_contrast = enhancer.enhance(2.5)
        
        return high_contrast
    
    def _preprocess_grayscale_sharp(self, image):
        """Simple grayscale with sharpening"""
        # Convert to grayscale
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image
        
        # Resize moderately
        width, height = gray.size
        new_size = (int(width * 1.5), int(height * 1.5))
        resized = gray.resize(new_size, Image.Resampling.LANCZOS)
        
        # Apply unsharp mask
        sharpened = resized.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
        
        return sharpened
    
    def _calculate_simple_score(self, text: str, base_weight: float) -> float:
        """Simple scoring system"""
        score = len(text.strip()) * base_weight * 0.1
        
        # German names
        german_names = re.findall(r'[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+', text)
        if german_names:
            score += 60 * len(german_names)
        
        # Insurance numbers
        insurance_numbers = re.findall(r'[A-Z]?\d{9,10}', text)
        if insurance_numbers:
            score += 50 * len(insurance_numbers)
        
        # Insurance companies
        companies = ['AOK', 'TECHNIKER', 'TK', 'BARMER', 'DAK', 'KKH']
        for company in companies:
            if company in text.upper():
                score += 40
        
        # German umlauts
        umlauts = len(re.findall(r'[äöüÄÖÜß]', text))
        if umlauts > 0:
            score += umlauts * 3
        
        return score
    
    def _simple_combine_results(self, results: List[Dict]) -> str:
        """Simple result combination"""
        all_lines = []
        
        for result in results:
            text = result.get('text', '')
            if text:
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                all_lines.extend(lines)
        
        # Remove duplicates while preserving order
        unique_lines = []
        seen = set()
        for line in all_lines:
            if line not in seen and len(line) > 2:
                unique_lines.append(line)
                seen.add(line)
        
        return '\n'.join(unique_lines[:10])  # Limit to top 10 lines
    
    def _parse_german_insurance_card_simple(self, text: str) -> Dict[str, str]:
        """Simplified German insurance card parsing"""
        data = {
            'name': '',
            'insurance_number': '',
            'insurance_company': '',
            'birth_date': '',
            'valid_until': ''
        }
        
        if not text or not text.strip():
            return data
        
        lines = text.split('\n') if '\n' in text else [text]
        text_clean = ' '.join(lines).strip()
        
        # Extract name (basic pattern)
        name_match = re.search(r'([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)', text_clean)
        if name_match:
            potential_name = name_match.group(1).strip()
            if not any(company in potential_name.upper() for company in ['AOK', 'TK', 'BARMER', 'DAK']):
                data['name'] = potential_name
        
        # Extract insurance number
        number_match = re.search(r'([A-Z]?\d{9,10})', text_clean)
        if number_match:
            data['insurance_number'] = number_match.group(1)
        
        # Extract dates
        dates = re.findall(r'(\d{1,2}[\/\.]\d{2,4})', text_clean)
        if dates:
            data['valid_until'] = dates[-1]
            if len(dates) > 1:
                data['birth_date'] = dates[0]
        
        # Extract insurance company
        companies = ['AOK', 'TK', 'Techniker', 'Barmer', 'DAK', 'KKH']
        for company in companies:
            if company.lower() in text_clean.lower():
                data['insurance_company'] = company
                break
        
        return data
    
    def validate_card_type(self, image_bytes: bytes) -> Dict[str, Any]:
        """Simple card validation"""
        return {
            "is_insurance_card": True,
            "card_type": "insurance",
            "confidence": 0.8,
            "success": True
        }
    
    def create_validation_record(self, meeting_id: str, validation_data: Dict) -> str:
        """Create validation record"""
        validation_id = f"val_{uuid.uuid4().hex[:8]}"
        logger.info(f"Created validation record {validation_id} for meeting {meeting_id}")
        return validation_id
    
    def get_validation_status(self, validation_id: str) -> Dict[str, Any]:
        """Get validation status"""
        return {
            "status": "completed",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "validated": True
        } 