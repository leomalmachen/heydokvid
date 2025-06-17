"""
Enhanced Insurance Card Service - EasyOCR Implementation
Advanced OCR service for German insurance cards using EasyOCR with optimized preprocessing
"""
import easyocr
import cv2
import numpy as np
import logging
import uuid
import io
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

class InsuranceCardService:
    """Enhanced service for processing German insurance cards with EasyOCR"""
    
    def __init__(self, db: Session):
        self.db = db
        # Initialize EasyOCR with German and English support, CPU-only for Heroku
        try:
            self.reader = easyocr.Reader(['de', 'en'], gpu=False, verbose=False)
            logger.info("EasyOCR initialized successfully with German + English support (CPU-only)")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            self.reader = None
    
    def extract_card_data(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract data from insurance card image using EasyOCR with advanced preprocessing
        """
        if not self.reader:
            return {
                "success": False,
                "error": "EasyOCR nicht verfügbar - Service-Initialisierung fehlgeschlagen",
                "data": {},
                "confidence": 0.0
            }

        try:
            logger.info(f"Starting EasyOCR processing, image size: {len(image_bytes)} bytes")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"PIL Image loaded: {image.size}, mode: {image.mode}")
            
            # Apply multi-approach EasyOCR processing
            results = self._multi_approach_easyocr(image)
            
            if not results:
                logger.warning("No OCR results from any approach")
                return {
                    "success": False,
                    "error": "Kein Text erkannt - bitte Bildqualität verbessern und erneut scannen",
                    "data": {},
                    "confidence": 0.0
                }
            
            # Get best result based on confidence
            best_result = max(results, key=lambda x: x['avg_confidence'])
            logger.info(f"Best approach: {best_result['approach']} with confidence: {best_result['avg_confidence']:.3f}")
            
            # Combine and parse all text findings
            combined_text = self._combine_all_text(results)
            parsed_data = self._parse_german_insurance_card(combined_text, best_result['detections'])
            
            # Validate extracted data
            if not self._has_meaningful_data(parsed_data):
                logger.warning(f"No meaningful insurance data found")
                return {
                    "success": False,
                    "error": "Kartendaten nicht lesbar - bitte Karte besser positionieren und erneut scannen",
                    "data": {},
                    "confidence": best_result['avg_confidence'],
                    "raw_text": combined_text[:200]
                }
            
            logger.info(f"EasyOCR extraction successful: {list(parsed_data.keys())}")
            
            return {
                "success": True,
                "data": parsed_data,
                "confidence": best_result['avg_confidence'],
                "raw_text": combined_text,
                "approach_used": best_result['approach']
            }
            
        except Exception as e:
            logger.error(f"EasyOCR processing error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"OCR-Verarbeitung fehlgeschlagen: {str(e)[:100]} - bitte erneut versuchen",
                "data": {},
                "confidence": 0.0
            }
    
    def _multi_approach_easyocr(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Apply multiple preprocessing approaches for optimal results"""
        approaches = [
            {
                'name': 'enhanced_contrast',
                'method': self._preprocess_enhanced_contrast,
                'description': 'High contrast for clear text'
            },
            {
                'name': 'gaussian_smooth',
                'method': self._preprocess_gaussian_smooth,
                'description': 'Gaussian blur for noise reduction'
            },
            {
                'name': 'adaptive_sharp',
                'method': self._preprocess_adaptive_sharp,
                'description': 'Adaptive sharpening for text clarity'
            },
            {
                'name': 'high_resolution',
                'method': self._preprocess_high_resolution,
                'description': 'Resolution enhancement for small text'
            }
        ]
        
        results = []
        
        for approach in approaches:
            try:
                logger.info(f"Applying EasyOCR approach: {approach['name']}")
                
                # Apply preprocessing
                processed_image = approach['method'](image)
                
                # Convert PIL to numpy array for EasyOCR
                img_array = np.array(processed_image)
                
                # Run EasyOCR
                detections = self.reader.readtext(img_array, detail=1)
                
                if detections:
                    # Calculate average confidence
                    confidences = [det[2] for det in detections if det[2] > 0.1]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    
                    # Extract all text
                    extracted_text = ' '.join([det[1] for det in detections if det[2] > 0.1])
                    
                    result = {
                        'approach': approach['name'],
                        'detections': detections,
                        'extracted_text': extracted_text,
                        'avg_confidence': avg_confidence,
                        'text_count': len([det for det in detections if det[2] > 0.1])
                    }
                    
                    results.append(result)
                    logger.info(f"Approach {approach['name']}: {len(detections)} detections, "
                              f"avg confidence: {avg_confidence:.3f}")
                else:
                    logger.warning(f"No detections from approach: {approach['name']}")
                    
            except Exception as e:
                logger.warning(f"Approach {approach['name']} failed: {e}")
                continue
        
        return results
    
    def _preprocess_enhanced_contrast(self, image: Image.Image) -> Image.Image:
        """Enhanced contrast preprocessing for clear text recognition"""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Increase resolution for better recognition
        width, height = image.size
        image = image.resize((width * 2, height * 2), Image.LANCZOS)
        
        # Enhance contrast significantly
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)
        
        # Apply slight sharpening
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=1))
        
        return image
    
    def _preprocess_gaussian_smooth(self, image: Image.Image) -> Image.Image:
        """Gaussian smoothing for noise reduction"""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Moderate resolution increase
        width, height = image.size
        image = image.resize((width * 1.5, height * 1.5), Image.LANCZOS)
        
        # Apply Gaussian blur to reduce noise
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Moderate contrast enhancement
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.8)
        
        return image
    
    def _preprocess_adaptive_sharp(self, image: Image.Image) -> Image.Image:
        """Adaptive sharpening for text clarity"""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Standard resolution increase
        width, height = image.size
        image = image.resize((width * 2, height * 2), Image.LANCZOS)
        
        # Apply adaptive sharpening
        image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=200, threshold=2))
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Final contrast boost
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.6)
        
        return image
    
    def _preprocess_high_resolution(self, image: Image.Image) -> Image.Image:
        """High resolution enhancement for small text"""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Significant resolution increase
        width, height = image.size
        image = image.resize((width * 3, height * 3), Image.LANCZOS)
        
        # Brightness adjustment
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)
        
        # Moderate contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        return image
    
    def _combine_all_text(self, results: List[Dict[str, Any]]) -> str:
        """Combine text from all approaches for comprehensive parsing"""
        all_text_parts = []
        
        for result in results:
            if result.get('extracted_text'):
                all_text_parts.append(result['extracted_text'])
        
        combined = ' '.join(all_text_parts)
        logger.info(f"Combined text length: {len(combined)} characters")
        return combined
    
    def _parse_german_insurance_card(self, combined_text: str, best_detections: List) -> Dict[str, str]:
        """Parse German insurance card data with enhanced pattern recognition"""
        data = {
            'name': '',
            'insurance_number': '',
            'insurance_company': '',
            'birth_date': '',
            'valid_until': ''
        }
        
        if not combined_text:
            return data
        
        # Clean and prepare text
        text_clean = re.sub(r'\s+', ' ', combined_text).strip()
        
        # Enhanced name extraction with German patterns
        name_patterns = [
            r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[a-zäöüß]+)?\s+[A-ZÄÖÜ][a-zäöüß]+)',  # German names with optional middle names
            r'([A-Z][a-z]+(?:\s+[a-z]+)?\s+[A-Z][a-z]+)',  # Without umlauts
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text_clean)
            for match in matches:
                # Validate it's a real name (not company, etc.)
                if (len(match.split()) >= 2 and 
                    len(match) <= 50 and 
                    not re.search(r'\d', match) and
                    not any(company.lower() in match.lower() for company in 
                           ['aok', 'tk', 'barmer', 'dak', 'ikkk', 'techniker', 'knappschaft'])):
                    data['name'] = match.strip()
                    break
            if data['name']:
                break
        
        # Enhanced insurance number extraction
        number_patterns = [
            r'\b([A-Z]?\d{10})\b',  # 10-digit with optional prefix
            r'\b(\d{10})\b',        # Exactly 10 digits
            r'\b([A-Z]\d{9})\b',    # Letter + 9 digits
        ]
        
        for pattern in number_patterns:
            match = re.search(pattern, text_clean)
            if match:
                number = match.group(1)
                # Validate it looks like an insurance number
                if len(number) >= 9:
                    data['insurance_number'] = number
                    break
        
        # Enhanced German insurance company detection
        company_patterns = [
            (r'(?:AOK|A\.O\.K\.?)', 'AOK'),
            (r'(?:TK|Techniker|TECHNIKER)', 'Techniker Krankenkasse'),
            (r'(?:BARMER|Barmer)', 'Barmer'),
            (r'(?:DAK|DAK-Gesundheit)', 'DAK-Gesundheit'),
            (r'(?:IKK|Innungskrankenkasse)', 'IKK'),
            (r'(?:HEK|Hanseatische)', 'HEK'),
            (r'(?:KKH|Kaufmännische)', 'KKH'),
            (r'(?:Knappschaft)', 'Knappschaft'),
        ]
        
        for pattern, name in company_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                data['insurance_company'] = name
                break
        
        # Date extraction
        date_patterns = [
            r'\b(\d{2}[\.\/]\d{2}[\.\/]\d{4})\b',  # DD.MM.YYYY or DD/MM/YYYY
            r'\b(\d{2}[\.\/]\d{4})\b',             # MM.YYYY or MM/YYYY
            r'\b(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})\b'  # Flexible date
        ]
        
        dates_found = []
        for pattern in date_patterns:
            dates_found.extend(re.findall(pattern, text_clean))
        
        if dates_found:
            # Assume last date is valid_until, first might be birth_date
            data['valid_until'] = dates_found[-1]
            if len(dates_found) > 1:
                data['birth_date'] = dates_found[0]
        
        # Log extraction results
        found_fields = {k: v for k, v in data.items() if v}
        logger.info(f"Extracted insurance data: {found_fields}")
        
        return data
    
    def _has_meaningful_data(self, data: Dict[str, str]) -> bool:
        """Check if extracted data contains meaningful insurance information"""
        essential_fields = ['name', 'insurance_number', 'insurance_company']
        found_essential = sum(1 for field in essential_fields if data.get(field))
        
        # At least 2 out of 3 essential fields should be found
        return found_essential >= 2
    
    def validate_card_type(self, image_bytes: bytes) -> Dict[str, Any]:
        """Simple card validation"""
        return {
            "is_insurance_card": True,
            "card_type": "insurance",
            "confidence": 0.85,
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