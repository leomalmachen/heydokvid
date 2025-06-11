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
from PIL import Image
import numpy as np

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
        Process image with OCR
        In production: integrate Tesseract or Google Vision API
        """
        try:
            # Simulate OCR processing
            # In production: use pytesseract or Google Vision API
            
            # Mock extracted text for demonstration
            mock_text = """
            Krankenversichertenkarte
            Max Mustermann
            A123456789
            Geb.: 01.01.1980
            AOK Bayern
            Gültig bis: 12/2025
            """
            
            # Extract structured data from text
            structured_data = self._parse_ocr_text(mock_text)
            
            return {
                "success": True,
                "data": structured_data,
                "raw_text": mock_text.strip()
            }
            
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_ocr_text(self, text: str) -> Dict[str, str]:
        """Parse OCR text to extract structured data"""
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            data = {
                "name": "",
                "insurance_number": "",
                "insurance_company": "",
                "birth_date": "",
                "valid_until": ""
            }
            
            # Simple parsing logic (in production: use regex patterns)
            for line in lines:
                line_lower = line.lower()
                
                # Name detection (usually after "Krankenversichertenkarte")
                if len(line.split()) == 2 and not any(char.isdigit() for char in line):
                    if not data["name"] and "kranken" not in line_lower:
                        data["name"] = line
                
                # Insurance number (starts with letter, followed by numbers)
                if len(line) >= 8 and line[0].isalpha() and line[1:].isdigit():
                    data["insurance_number"] = line
                
                # Birth date
                if "geb" in line_lower and ":" in line:
                    data["birth_date"] = line.split(":")[-1].strip()
                
                # Valid until
                if "gültig" in line_lower and "/" in line:
                    data["valid_until"] = line.split(":")[-1].strip()
                
                # Insurance company (common names)
                if any(company in line_lower for company in ["aok", "tk", "barmer", "dak", "kkh"]):
                    data["insurance_company"] = line
            
            return data
            
        except Exception as e:
            logger.error(f"OCR text parsing error: {e}")
            return {}
    
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