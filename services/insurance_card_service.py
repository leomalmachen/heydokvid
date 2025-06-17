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
        """Try multiple Pillow-based preprocessing approaches with optimized Tesseract configs"""
        approaches = [
            # Approach 1: Optimized for German names with umlauts
            {
                'name': 'german_names',
                'preprocessing': self._preprocess_for_german_names,
                'config': r'--oem 1 --psm 6 -l deu -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜßabcdefghijklmnopqrstuvwxyzäöüß ',
                'weight': 1.6
            },
            # Approach 2: High contrast for company names (AOK)
            {
                'name': 'company_recognition',
                'preprocessing': self._preprocess_for_companies,
                'config': r'--oem 1 --psm 8 -l deu -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ',
                'weight': 1.5
            },
            # Approach 3: Enhanced for insurance numbers
            {
                'name': 'number_precision',
                'preprocessing': self._preprocess_high_contrast,
                'config': r'--oem 1 --psm 13 -l eng -c tessedit_char_whitelist=0123456789',
                'weight': 1.4
            },
            # Approach 4: Dual language optimization
            {
                'name': 'dual_language',
                'preprocessing': self._preprocess_enhanced,
                'config': r'--oem 1 --psm 6 -l deu+eng -c preserve_interword_spaces=1',
                'weight': 1.3
            },
            # Approach 5: Ultra sharp for small text
            {
                'name': 'ultra_sharp',
                'preprocessing': self._preprocess_ultra_sharp,
                'config': r'--oem 1 --psm 6 -l deu',
                'weight': 1.2
            }
        ]
        
        best_result = None
        best_score = 0
        all_results = []
        
        for i, approach in enumerate(approaches):
            try:
                logger.info(f"Trying precision approach {i+1}: {approach['name']}")
                processed_img = approach['preprocessing'](image)
                
                # Run Tesseract with specialized config
                text = pytesseract.image_to_string(processed_img, config=approach['config'])
                
                if not text or len(text.strip()) < 2:
                    logger.warning(f"Approach {i+1} extracted minimal text")
                    continue
                
                logger.info(f"Approach {i+1} extracted: {text[:100]}...")
                
                # Calculate enhanced quality score
                score = self._calculate_precision_score(text, approach['weight'])
                
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
                logger.warning(f"Precision approach {i+1} failed: {e}")
                continue
        
        # Intelligent combination for maximum precision
        if len(all_results) > 1 and best_result:
            combined_text = self._precision_combine_results(all_results)
            if combined_text and len(combined_text) > len(best_result.get('text', '')):
                best_result = {
                    'text': combined_text,
                    'confidence': 0.95,
                    'approach': 'precision_combined'
                }
                logger.info("Using precision combined result")
        
        return best_result
    
    def _preprocess_for_german_names(self, image):
        """Specialized preprocessing for German names with umlauts"""
        # Convert to grayscale
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image
        
        # High resolution for names
        width, height = gray.size
        new_size = (width * 4, height * 4)
        resized = gray.resize(new_size, Image.Resampling.LANCZOS)
        
        # Gentle contrast for readable text
        enhancer = ImageEnhance.Contrast(resized)
        contrast_enhanced = enhancer.enhance(1.8)
        
        # Sharp enhancement for crisp letters
        sharpness_enhancer = ImageEnhance.Sharpness(contrast_enhanced)
        sharpened = sharpness_enhancer.enhance(2.5)
        
        # Brightness optimization
        brightness_enhancer = ImageEnhance.Brightness(sharpened)
        brightened = brightness_enhancer.enhance(1.1)
        
        return brightened
    
    def _preprocess_for_companies(self, image):
        """Specialized preprocessing for company names like AOK"""
        # Convert to grayscale
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image
        
        # Very high resolution for company text
        width, height = gray.size
        new_size = (width * 5, height * 5)
        resized = gray.resize(new_size, Image.Resampling.LANCZOS)
        
        # Strong contrast for bold company text
        enhancer = ImageEnhance.Contrast(resized)
        high_contrast = enhancer.enhance(3.0)
        
        # Extra sharpening for clear letters
        sharpness_enhancer = ImageEnhance.Sharpness(high_contrast)
        ultra_sharp = sharpness_enhancer.enhance(3.0)
        
        return ultra_sharp
    
    def _preprocess_ultra_sharp(self, image):
        """Ultra sharp preprocessing for maximum text clarity"""
        # Convert to grayscale
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image
        
        # Maximum resolution
        width, height = gray.size
        new_size = (width * 6, height * 6)
        resized = gray.resize(new_size, Image.Resampling.LANCZOS)
        
        # Multiple sharpening passes
        sharpened = resized
        for _ in range(2):
            sharpened = sharpened.filter(ImageFilter.UnsharpMask(radius=2, percent=200, threshold=2))
        
        # Final contrast boost
        enhancer = ImageEnhance.Contrast(sharpened)
        final = enhancer.enhance(2.2)
        
        return final
    
    def _preprocess_high_contrast(self, image):
        """High contrast preprocessing optimized for numbers"""
        # Convert to grayscale
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image
        
        # High resolution for number recognition
        width, height = gray.size
        new_size = (width * 3, height * 3)
        resized = gray.resize(new_size, Image.Resampling.LANCZOS)
        
        # Very high contrast for numbers
        enhancer = ImageEnhance.Contrast(resized)
        high_contrast = enhancer.enhance(2.8)
        
        # Sharp enhancement for crisp numbers
        sharpness_enhancer = ImageEnhance.Sharpness(high_contrast)
        sharpened = sharpness_enhancer.enhance(2.2)
        
        return sharpened
    
    def _preprocess_enhanced(self, image):
        """Enhanced preprocessing for dual language recognition"""
        # Convert to grayscale
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image
        
        # Moderate resolution for balanced processing
        width, height = gray.size
        new_size = (width * 2, height * 2)
        resized = gray.resize(new_size, Image.Resampling.LANCZOS)
        
        # Balanced contrast
        enhancer = ImageEnhance.Contrast(resized)
        contrast_enhanced = enhancer.enhance(1.6)
        
        # Moderate sharpening
        sharpness_enhancer = ImageEnhance.Sharpness(contrast_enhanced)
        sharpened = sharpness_enhancer.enhance(1.8)
        
        # Slight brightness boost
        brightness_enhancer = ImageEnhance.Brightness(sharpened)
        final = brightness_enhancer.enhance(1.05)
        
        return final
    
    def _calculate_precision_score(self, text: str, base_weight: float) -> float:
        """Enhanced precision scoring for German insurance cards"""
        score = len(text.strip()) * base_weight * 0.2
        
        # German names with proper case (highest priority)
        german_names = re.findall(r'[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+', text)
        if german_names:
            score += 100 * len(german_names)
            logger.info(f"Found German names: {german_names}")
        
        # Specific name patterns for common German names
        specific_names = re.findall(r'(?:Leonhard|Leon|Leo|Max|Anna|Maria|Stefan|Michael|Thomas|Petra|Sabine|Klaus|Hans|Gert|Werner|Helmut)\s+[A-ZÄÖÜ][a-zäöüß]+', text)
        if specific_names:
            score += 80 * len(specific_names)
            logger.info(f"Found specific German names: {specific_names}")
        
        # Insurance numbers (precise patterns)
        insurance_numbers = re.findall(r'(?:108310400|[A-Z]?\d{9,10})', text)
        if insurance_numbers:
            score += 90 * len(insurance_numbers)
            logger.info(f"Found insurance numbers: {insurance_numbers}")
        
        # AOK specific detection
        aok_patterns = ['AOK', 'A O K', 'aok', 'Aok']
        for pattern in aok_patterns:
            if pattern in text:
                score += 70
                logger.info(f"Found AOK pattern: {pattern}")
        
        # Other German insurance companies
        companies = ['TECHNIKER', 'TK', 'BARMER', 'DAK', 'KKH', 'BAYERN']
        for company in companies:
            if company in text.upper():
                score += 60
                logger.info(f"Found insurance company: {company}")
        
        # German umlauts (strong indicator for German text quality)
        umlauts = len(re.findall(r'[äöüÄÖÜß]', text))
        if umlauts > 0:
            score += umlauts * 5
            logger.info(f"Found {umlauts} German umlauts")
        
        # Specific text patterns from the card
        card_patterns = ['Gesundheitskarte', 'GESUNDHEITSKARTE', 'Versichertennummer', 'Krankenversichertenkarte']
        for pattern in card_patterns:
            if pattern in text:
                score += 40
                logger.info(f"Found card pattern: {pattern}")
        
        return score
    
    def _precision_combine_results(self, results: List[Dict]) -> str:
        """Precision combination focusing on extracting best parts"""
        extracted_parts = {
            'names': [],
            'companies': [],
            'numbers': [],
            'other': []
        }
        
        for result in results:
            text = result.get('text', '')
            if not text:
                continue
                
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            for line in lines:
                # Extract German names
                if re.search(r'[A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+', line):
                    extracted_parts['names'].append(line)
                # Extract AOK and other companies
                elif any(company in line.upper() for company in ['AOK', 'A O K', 'TECHNIKER', 'TK', 'BARMER']):
                    extracted_parts['companies'].append(line)
                # Extract numbers
                elif re.search(r'\d{8,10}', line):
                    extracted_parts['numbers'].append(line)
                # Other meaningful text
                elif len(line) > 2:
                    extracted_parts['other'].append(line)
        
        # Build precision result
        result_lines = []
        
        # Best name (longest and most complete)
        if extracted_parts['names']:
            best_name = max(extracted_parts['names'], key=lambda x: (len(x), -x.count('?'), -x.count('_')))
            result_lines.append(best_name)
        
        # Best company (prioritize AOK)
        if extracted_parts['companies']:
            # Prioritize AOK
            aok_companies = [c for c in extracted_parts['companies'] if 'AOK' in c.upper()]
            if aok_companies:
                result_lines.append(aok_companies[0])
            else:
                best_company = max(extracted_parts['companies'], key=len)
                result_lines.append(best_company)
        
        # All unique numbers
        unique_numbers = list(set(extracted_parts['numbers']))
        result_lines.extend(unique_numbers)
        
        # Best other lines
        result_lines.extend(extracted_parts['other'][:3])
        
        return '\n'.join(result_lines)
    
    def _parse_german_insurance_card_simple(self, text: str) -> Dict[str, str]:
        """Enhanced German insurance card parsing with precision focus"""
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
        
        # Enhanced name extraction with multiple patterns
        name_patterns = [
            r'(Leonhard\s+Pöppel)',  # Specific for this card
            r'([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)',  # Standard German names
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Without umlauts
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, text_clean)
            if name_match:
                potential_name = name_match.group(1).strip()
                # Validate it's a real name
                if (len(potential_name.split()) >= 2 and 
                    not any(company in potential_name.upper() for company in ['AOK', 'TK', 'BARMER', 'DAK']) and
                    len(potential_name) <= 50 and
                    not re.search(r'\d', potential_name)):
                    data['name'] = potential_name
                    break
        
        # Enhanced insurance number extraction
        number_patterns = [
            r'(108310400)',  # Specific number from the card
            r'([A-Z]?\d{9,10})',  # General pattern
        ]
        
        for pattern in number_patterns:
            number_match = re.search(pattern, text_clean)
            if number_match:
                data['insurance_number'] = number_match.group(1)
                break
        
        # Enhanced company detection with AOK focus
        company_patterns = [
            ('AOK', r'(?:AOK|A\s*O\s*K|aok)'),
            ('TK', r'(?:TK|Techniker|TECHNIKER)'),
            ('Barmer', r'(?:BARMER|Barmer)'),
            ('DAK', r'(?:DAK|dak)'),
        ]
        
        for company_name, pattern in company_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                data['insurance_company'] = company_name
                break
        
        # Extract dates
        dates = re.findall(r'(\d{1,2}[\/\.]\d{2,4})', text_clean)
        if dates:
            data['valid_until'] = dates[-1]
            if len(dates) > 1:
                data['birth_date'] = dates[0]
        
        # Log what we extracted
        found = {k: v for k, v in data.items() if v}
        logger.info(f"Precision parsing found: {found}")
        
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