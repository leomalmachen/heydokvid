"""
Insurance Card Service for automatic card detection and OCR processing
"""
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from database import get_db
import uuid
from datetime import datetime
import logging
import io
import base64
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2
import pytesseract
import re

logger = logging.getLogger(__name__)

class InsuranceCardService:
    """Service for automatic insurance card detection and processing"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_card_type(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze image to determine if it's an insurance card
        Returns card type detection result
        """
        try:
            # Convert bytes to PIL Image for analysis
            image = Image.open(io.BytesIO(image_data))
            
            # Basic image validation
            if image.width < 100 or image.height < 100:
                return {
                    "is_insurance_card": False,
                    "card_type": "unknown",
                    "confidence": 0.0,
                    "error": "Image too small"
                }
            
            # Simulate card type detection (in production: use computer vision)
            card_detection = self._analyze_card_features(image)
            
            return card_detection
            
        except Exception as e:
            logger.error(f"Card type validation error: {e}")
            return {
                "is_insurance_card": False,
                "card_type": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _analyze_card_features(self, image: Image) -> Dict[str, Any]:
        """
        Analyze card features to determine type
        In production: use computer vision algorithms
        """
        try:
            # Convert to numpy array for analysis
            img_array = np.array(image)
            
            # Basic color analysis
            color_profile = self.extract_color_profile(img_array)
            
            # Text region detection (simplified)
            has_text_regions = self._detect_text_regions(img_array)
            
            # Card size ratio analysis
            aspect_ratio = image.width / image.height
            
            # Insurance card characteristics
            is_likely_insurance = (
                1.5 < aspect_ratio < 1.7 and  # Standard ID card ratio
                color_profile.get("has_blue_elements", False) and
                has_text_regions
            )
            
            if is_likely_insurance:
                return {
                    "is_insurance_card": True,
                    "card_type": "insurance",
                    "confidence": 0.85,
                    "features": {
                        "aspect_ratio": aspect_ratio,
                        "color_profile": color_profile,
                        "has_text": has_text_regions
                    }
                }
            else:
                # Determine other card types
                if color_profile.get("has_gold_elements", False):
                    card_type = "id"
                elif color_profile.get("has_metallic_elements", False):
                    card_type = "credit"
                else:
                    card_type = "other"
                
                return {
                    "is_insurance_card": False,
                    "card_type": card_type,
                    "confidence": 0.75,
                    "features": {
                        "aspect_ratio": aspect_ratio,
                        "color_profile": color_profile,
                        "has_text": has_text_regions
                    }
                }
                
        except Exception as e:
            logger.error(f"Card feature analysis error: {e}")
            return {
                "is_insurance_card": False,
                "card_type": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def extract_color_profile(self, img_array: np.ndarray) -> Dict[str, Any]:
        """Extract color characteristics from image"""
        try:
            # Convert to RGB if needed
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                # Calculate color statistics
                mean_colors = np.mean(img_array, axis=(0, 1))
                
                # Detect dominant colors
                has_blue_elements = mean_colors[2] > mean_colors[0] and mean_colors[2] > mean_colors[1]
                has_green_elements = mean_colors[1] > mean_colors[0] and mean_colors[1] > mean_colors[2]
                has_gold_elements = mean_colors[0] > 180 and mean_colors[1] > 150 and mean_colors[2] < 100
                
                return {
                    "mean_rgb": mean_colors.tolist(),
                    "has_blue_elements": bool(has_blue_elements),
                    "has_green_elements": bool(has_green_elements),
                    "has_gold_elements": bool(has_gold_elements),
                    "has_metallic_elements": False  # Simplified
                }
            
            return {"error": "Invalid image format"}
            
        except Exception as e:
            logger.error(f"Color profile extraction error: {e}")
            return {"error": str(e)}
    
    def _detect_text_regions(self, img_array: np.ndarray) -> bool:
        """
        Simple text region detection
        In production: use OpenCV or specialized text detection
        """
        try:
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            
            # Simple edge detection (Laplacian approximation)
            edges = np.abs(np.gradient(gray)).sum()
            
            # If there are many edges, likely contains text
            return edges > gray.size * 10  # Threshold
            
        except Exception as e:
            logger.error(f"Text region detection error: {e}")
            return False
    
    def extract_card_data(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract text data from insurance card using OCR
        """
        try:
            # Validate card type first
            card_validation = self.validate_card_type(image_data)
            
            if not card_validation.get("is_insurance_card", False):
                return {
                    "success": False,
                    "error": f"Not an insurance card: {card_validation.get('card_type', 'unknown')}",
                    "card_validation": card_validation
                }
            
            # Process with OCR
            ocr_result = self._process_with_ocr(image_data)
            
            if ocr_result["success"]:
                # Validate extracted data
                validated_data = self.validate_extracted_data(ocr_result["data"])
                
                return {
                    "success": True,
                    "data": validated_data,
                    "card_validation": card_validation,
                    "raw_ocr": ocr_result.get("raw_text", "")
                }
            else:
                return {
                    "success": False,
                    "error": ocr_result.get("error", "OCR processing failed"),
                    "card_validation": card_validation
                }
                
        except Exception as e:
            logger.error(f"Card data extraction error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_with_ocr(self, image_data: bytes) -> Dict[str, Any]:
        """
        Process image with OCR using pytesseract with image preprocessing
        """
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Preprocess image for better OCR
            preprocessed_image = self._preprocess_for_ocr(image)
            
            # Configure Tesseract for German insurance cards
            custom_config = r'--oem 3 --psm 6 -l deu'
            
            # Extract text using pytesseract
            try:
                raw_text = pytesseract.image_to_string(
                    preprocessed_image, 
                    config=custom_config
                )
            except pytesseract.TesseractNotFoundError:
                logger.error("Tesseract not found - OCR nicht verfügbar")
                return {
                    "success": False,
                    "error": "OCR-Engine nicht installiert. Bitte Administrator kontaktieren."
                }
            except pytesseract.TesseractError as te:
                logger.error(f"Tesseract error: {te}")
                return {
                    "success": False,
                    "error": "OCR-Verarbeitung fehlgeschlagen. Bitte Bildqualität prüfen."
                }
            
            logger.info(f"OCR extracted text: {raw_text[:200]}...")  # Log first 200 chars
            
            if not raw_text.strip():
                return {
                    "success": False,
                    "error": "Kein Text erkannt - bitte Bildqualität prüfen"
                }
            
            # Parse structured data from text
            structured_data = self._parse_ocr_text(raw_text)
            
            # Calculate confidence based on extracted data quality
            confidence = self._calculate_confidence(structured_data, raw_text)
            
            return {
                "success": True,
                "data": structured_data,
                "raw_text": raw_text.strip(),
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return {
                "success": False,
                "error": f"OCR-Verarbeitung fehlgeschlagen: {str(e)}"
            }
    
    def _preprocess_for_ocr(self, image: Image) -> Image:
        """
        Preprocess image for better OCR results
        """
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too small (insurance cards should be readable at decent size)
            width, height = image.size
            if width < 600:  # Minimum width for good OCR
                scale_factor = 600 / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            
            # Convert to OpenCV format for advanced preprocessing
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Apply denoising
            cv_image = cv2.fastNlMeansDenoisingColored(cv_image, None, 10, 10, 7, 21)
            
            # Convert to grayscale for better text detection
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding for better text contrast
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Apply morphological operations to clean up text
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
            
            # Convert back to PIL Image
            final_image = Image.fromarray(processed)
            
            # Additional PIL enhancements
            # Sharpen text
            final_image = final_image.filter(ImageFilter.SHARPEN)
            
            # Increase contrast
            enhancer = ImageEnhance.Contrast(final_image)
            final_image = enhancer.enhance(1.2)
            
            logger.info("Image preprocessing completed")
            return final_image
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            # Return original image if preprocessing fails
            return image
    
    def _parse_ocr_text(self, text: str) -> Dict[str, str]:
        """Parse OCR text to extract structured data from German insurance cards"""
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            data = {
                "name": "",
                "insurance_number": "",
                "insurance_company": "",
                "birth_date": "",
                "valid_until": ""
            }
            
            logger.info(f"Parsing {len(lines)} lines of OCR text")
            
            # Enhanced parsing logic for German insurance cards
            for i, line in enumerate(lines):
                line_clean = line.strip()
                line_lower = line_clean.lower()
                
                # Skip header lines
                if any(header in line_lower for header in [
                    'krankenversichertenkarte', 'versichertenkarte', 'european health',
                    'bundesrepublik', 'deutschland', 'germany'
                ]):
                    continue
                
                # Name detection - look for typical name patterns
                if not data["name"] and self._is_likely_name(line_clean):
                    data["name"] = line_clean
                    logger.info(f"Found name: {data['name']}")
                    continue
                
                # Insurance number - German format (letter + 9 digits or 10 digits)
                if not data["insurance_number"]:
                    ins_match = re.search(r'([A-Z]\d{9}|\d{10})', line_clean)
                    if ins_match:
                        data["insurance_number"] = ins_match.group(1)
                        logger.info(f"Found insurance number: {data['insurance_number']}")
                        continue
                
                # Birth date patterns
                if not data["birth_date"]:
                    birth_patterns = [
                        r'(?:geb\.?:?\s*)?(\d{1,2}\.?\d{1,2}\.?\d{2,4})',
                        r'(?:geboren:?\s*)?(\d{1,2}/\d{1,2}/\d{2,4})',
                        r'(?:birth:?\s*)?(\d{1,2}-\d{1,2}-\d{2,4})'
                    ]
                    for pattern in birth_patterns:
                        birth_match = re.search(pattern, line_clean, re.IGNORECASE)
                        if birth_match:
                            data["birth_date"] = birth_match.group(1)
                            logger.info(f"Found birth date: {data['birth_date']}")
                            break
                
                # Valid until patterns
                if not data["valid_until"]:
                    valid_patterns = [
                        r'(?:gültig bis:?\s*)?(\d{1,2}/\d{2,4})',
                        r'(?:bis:?\s*)?(\d{1,2}\.\d{2,4})',
                        r'(?:valid until:?\s*)?(\d{1,2}-\d{2,4})'
                    ]
                    for pattern in valid_patterns:
                        valid_match = re.search(pattern, line_clean, re.IGNORECASE)
                        if valid_match:
                            data["valid_until"] = valid_match.group(1)
                            logger.info(f"Found valid until: {data['valid_until']}")
                            break
                
                # Insurance company detection
                if not data["insurance_company"] and self._is_likely_insurance_company(line_clean):
                    data["insurance_company"] = line_clean
                    logger.info(f"Found insurance company: {data['insurance_company']}")
                    continue
            
            logger.info(f"OCR parsing result: {data}")
            return data
            
        except Exception as e:
            logger.error(f"OCR text parsing error: {e}")
            return {
                "name": "Parsing-Fehler",
                "insurance_number": "Nicht erkannt",
                "insurance_company": "Nicht erkannt",
                "birth_date": "",
                "valid_until": ""
            }
    
    def _is_likely_name(self, text: str) -> bool:
        """Check if text looks like a person's name"""
        if not text or len(text) < 3 or len(text) > 50:
            return False
        
        # Should contain only letters, spaces, common German characters, and hyphens
        if not re.match(r'^[A-Za-zÄÖÜäöüß\s\-\.]+$', text):
            return False
        
        words = text.split()
        if len(words) < 2 or len(words) > 4:
            return False
        
        # Each word should be reasonable name length
        for word in words:
            if len(word) < 2 or len(word) > 20:
                return False
        
        # At least one word should start with uppercase (typical for names)
        if not any(word[0].isupper() for word in words):
            return False
        
        return True
    
    def _is_likely_insurance_company(self, text: str) -> bool:
        """Check if text looks like an insurance company name"""
        if not text or len(text) < 3 or len(text) > 50:
            return False
        
        # Known German insurance company patterns
        insurance_keywords = [
            'aok', 'tk', 'techniker', 'barmer', 'dak', 'kkh', 'hek', 
            'pronova', 'bkk', 'ikk', 'knappschaft', 'svlfg', 'continentale',
            'debeka', 'signal', 'hansemerkur', 'bavaria', 'allianz'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in insurance_keywords)
    
    def _calculate_confidence(self, data: Dict[str, str], raw_text: str) -> float:
        """Calculate confidence score based on extracted data quality"""
        confidence = 0.0
        
        # Base confidence from text length and clarity
        if len(raw_text.strip()) > 50:
            confidence += 0.3
        
        # Confidence boost for each successfully extracted field
        if data.get("name") and data["name"] != "Nicht erkannt":
            confidence += 0.25
        
        if data.get("insurance_number") and data["insurance_number"] != "Nicht erkannt":
            # Validate insurance number format
            if re.match(r'^[A-Z]\d{9}$|^\d{10}$', data["insurance_number"]):
                confidence += 0.25
            else:
                confidence += 0.1
        
        if data.get("insurance_company") and data["insurance_company"] != "Nicht erkannt":
            confidence += 0.15
        
        if data.get("birth_date"):
            confidence += 0.1
        
        if data.get("valid_until"):
            confidence += 0.1
        
        # Cap confidence at reasonable maximum
        return min(confidence, 0.95)
    
    def validate_extracted_data(self, data: Dict[str, str]) -> Dict[str, str]:
        """Validate and clean extracted data"""
        try:
            validated = {}
            
            # Name validation
            name = data.get("name", "").strip()
            if name and len(name.split()) >= 2:
                validated["name"] = name
            else:
                validated["name"] = ""
            
            # Insurance number validation (German format)
            ins_number = data.get("insurance_number", "").strip()
            if ins_number and len(ins_number) == 10 and ins_number[0].isalpha():
                validated["insurance_number"] = ins_number
            else:
                validated["insurance_number"] = ""
            
            # Insurance company
            validated["insurance_company"] = data.get("insurance_company", "").strip()
            
            # Birth date
            validated["birth_date"] = data.get("birth_date", "").strip()
            
            # Valid until
            validated["valid_until"] = data.get("valid_until", "").strip()
            
            return validated
            
        except Exception as e:
            logger.error(f"Data validation error: {e}")
            return data
    
    def create_validation_record(self, meeting_id: str, extracted_data: Dict[str, Any]) -> str:
        """
        Create a validation record in the database
        Returns validation ID
        """
        try:
            validation_id = str(uuid.uuid4())
            
            # In production: save to database
            # For now, just log the validation
            logger.info(f"Insurance card validation created: {validation_id} for meeting {meeting_id}")
            logger.info(f"Extracted data: {extracted_data}")
            
            return validation_id
            
        except Exception as e:
            logger.error(f"Validation record creation error: {e}")
            raise
    
    def get_validation_status(self, validation_id: str) -> Dict[str, Any]:
        """Get validation status by ID"""
        try:
            # In production: query database
            # For now, return mock status
            return {
                "id": validation_id,
                "status": "completed",
                "created_at": datetime.utcnow().isoformat(),
                "validated": True
            }
            
        except Exception as e:
            logger.error(f"Get validation status error: {e}")
            return {"error": str(e)} 