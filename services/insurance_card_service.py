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
import time
import os

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
        Process image with OCR using pytesseract with ENHANCED image preprocessing and debugging
        """
        try:
            logger.info(f"🔍 ENHANCED OCR: Starting deep analysis... (image size: {len(image_data)} bytes)")
            start_time = time.time()
            
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))
            logger.info(f"📸 Image loaded: {image.size[0]}x{image.size[1]} pixels, mode: {image.mode}")
            
            # SAVE ORIGINAL IMAGE FOR DEBUGGING
            debug_dir = "/tmp/ocr_debug"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            timestamp = int(time.time())
            original_path = f"{debug_dir}/original_{timestamp}.png"
            image.save(original_path)
            logger.info(f"💾 Original image saved: {original_path}")
            
            # ENHANCED: Multiple preprocessing approaches with different strategies
            preprocessed_versions = self._create_multiple_preprocessed_versions(image, debug_dir, timestamp)
            logger.info(f"✅ Created {len(preprocessed_versions)} preprocessed versions")
            
            # ENHANCED: Extended OCR configurations for better results
            ocr_configs = [
                # High precision configs
                {'config': r'--oem 3 --psm 6 -l deu', 'description': 'German PSM 6 (uniform text)', 'weight': 1.0},
                {'config': r'--oem 3 --psm 8 -l deu', 'description': 'German PSM 8 (single word)', 'weight': 0.8},
                {'config': r'--oem 3 --psm 7 -l deu', 'description': 'German PSM 7 (single text line)', 'weight': 0.9},
                {'config': r'--oem 3 --psm 3 -l deu', 'description': 'German PSM 3 (auto)', 'weight': 0.7},
                {'config': r'--oem 3 --psm 4 -l deu', 'description': 'German PSM 4 (single column)', 'weight': 0.8},
                # Fallback configs
                {'config': r'--oem 3 --psm 6 -l eng+deu', 'description': 'German+English PSM 6', 'weight': 0.6},
                {'config': r'--oem 1 --psm 6 -l deu', 'description': 'German LSTM PSM 6', 'weight': 0.7},
                {'config': r'--oem 3 --psm 13 -l deu', 'description': 'German PSM 13 (raw line)', 'weight': 0.5},
            ]
            
            best_result = None
            best_score = 0
            all_attempts = []
            
            # Try each preprocessing version with each OCR config
            total_combinations = len(preprocessed_versions) * len(ocr_configs)
            current_attempt = 0
            
            logger.info(f"🧠 Starting {total_combinations} OCR attempts (this will take 5-15 seconds)...")
            
            for preprocess_name, preprocessed_image in preprocessed_versions:
                for i, config_info in enumerate(ocr_configs):
                    current_attempt += 1
                    try:
                        logger.info(f"🔄 Attempt {current_attempt}/{total_combinations}: {preprocess_name} + {config_info['description']}")
                        
                        # Add small delay to prevent overwhelming the system
                        time.sleep(0.1)
                        
                        # Extract text using pytesseract
                        raw_text = pytesseract.image_to_string(
                            preprocessed_image, 
                            config=config_info['config']
                        )
                        
                        if raw_text and raw_text.strip():
                            # Calculate weighted confidence score
                            base_confidence = self._calculate_text_confidence(raw_text)
                            weighted_score = base_confidence * config_info['weight']
                            
                            attempt = {
                                'preprocessing': preprocess_name,
                                'config': config_info['description'],
                                'raw_text': raw_text.strip(),
                                'confidence': base_confidence,
                                'weighted_score': weighted_score,
                                'text_length': len(raw_text.strip()),
                                'attempt_num': current_attempt
                            }
                            all_attempts.append(attempt)
                            
                            logger.info(f"📊 Attempt {current_attempt}: {len(raw_text.strip())} chars, confidence: {base_confidence:.2f}, score: {weighted_score:.2f}")
                            logger.info(f"📝 Text preview: {raw_text.strip()[:80]}...")
                            
                            if weighted_score > best_score:
                                best_result = attempt
                                best_score = weighted_score
                                logger.info(f"✅ NEW BEST RESULT: {preprocess_name} + {config_info['description']} (score: {weighted_score:.2f})")
                            
                            # If we get excellent results, still continue but log it
                            if weighted_score > 0.8 and len(raw_text.strip()) > 100:
                                logger.info(f"🎯 Excellent result found, but continuing full analysis...")
                                
                        else:
                            logger.debug(f"⚠️ Attempt {current_attempt} produced no text")
                            
                    except pytesseract.TesseractNotFoundError:
                        logger.error("❌ Tesseract not found - OCR not available")
                        return {
                            "success": False,
                            "error": "OCR-Engine nicht installiert. Bitte Administrator kontaktieren."
                        }
                    except pytesseract.TesseractError as te:
                        logger.warning(f"⚠️ Tesseract error on attempt {current_attempt}: {te}")
                        continue  # Try next config
                    except Exception as e:
                        logger.warning(f"⚠️ Attempt {current_attempt} failed: {e}")
                        continue  # Try next config
            
            total_time = time.time() - start_time
            
            # Log comprehensive results
            logger.info(f"📋 ANALYSIS COMPLETE: {len(all_attempts)} successful attempts out of {total_combinations} total ({total_time:.1f}s)")
            
            # Sort attempts by score for analysis
            sorted_attempts = sorted(all_attempts, key=lambda x: x['weighted_score'], reverse=True)
            logger.info("🏆 TOP 3 RESULTS:")
            for i, attempt in enumerate(sorted_attempts[:3]):
                logger.info(f"   #{i+1}: {attempt['preprocessing']} + {attempt['config']} (score: {attempt['weighted_score']:.2f})")
            
            if not best_result:
                logger.error(f"❌ ALL {total_combinations} OCR ATTEMPTS FAILED")
                # Save debug info
                debug_info = {
                    "total_attempts": total_combinations,
                    "preprocessing_versions": len(preprocessed_versions),
                    "ocr_configs": len(ocr_configs),
                    "analysis_time": total_time,
                    "original_image_path": original_path
                }
                return {
                    "success": False,
                    "error": f"Keine Texterkennung möglich nach {total_combinations} Versuchen. Debug-Bilder gespeichert in {debug_dir}",
                    "debug_info": debug_info
                }
            
            raw_text = best_result['raw_text']
            logger.info(f"🏆 FINAL RESULT: {best_result['preprocessing']} + {best_result['config']}")
            logger.info(f"📊 Best score: {best_score:.2f}, Text length: {len(raw_text)} chars")
            logger.info(f"📄 COMPLETE TEXT:\n{raw_text}")
            
            # Parse structured data from best text
            structured_data = self._parse_ocr_text(raw_text)
            logger.info(f"📊 Parsed structured data: {structured_data}")
            
            # Enhanced confidence calculation
            final_confidence = self._calculate_final_confidence(structured_data, raw_text, best_result['confidence'])
            
            # Save successful result for debugging
            success_path = f"{debug_dir}/success_{timestamp}.txt"
            with open(success_path, 'w', encoding='utf-8') as f:
                f.write(f"SUCCESSFUL OCR RESULT\n")
                f.write(f"Method: {best_result['preprocessing']} + {best_result['config']}\n")
                f.write(f"Score: {best_score:.2f}\n")
                f.write(f"Final Confidence: {final_confidence:.2f}\n")
                f.write(f"Analysis Time: {total_time:.1f}s\n")
                f.write(f"Attempts: {len(all_attempts)}/{total_combinations}\n\n")
                f.write(f"RAW TEXT:\n{raw_text}\n\n")
                f.write(f"STRUCTURED DATA:\n{structured_data}")
            
            logger.info(f"💾 Success log saved: {success_path}")
            
            return {
                "success": True,
                "data": structured_data,
                "raw_text": raw_text,
                "confidence": final_confidence,
                "ocr_attempts": len(all_attempts),
                "total_combinations": total_combinations,
                "best_method": f"{best_result['preprocessing']} + {best_result['config']}",
                "analysis_time": total_time,
                "debug_info": {
                    "debug_dir": debug_dir,
                    "original_image": original_path,
                    "success_log": success_path
                }
            }
            
        except Exception as e:
            logger.error(f"❌ CRITICAL OCR ERROR: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Kritischer OCR-Fehler: {str(e)}"
            }
    
    def _create_multiple_preprocessed_versions(self, image: Image, debug_dir: str, timestamp: int) -> list:
        """Create multiple preprocessed versions of the image for better OCR success"""
        versions = []
        
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Version 1: Original preprocessing (existing method)
            try:
                processed_1 = self._preprocess_for_ocr(image)
                processed_1.save(f"{debug_dir}/preprocess_original_{timestamp}.png")
                versions.append(("original_method", processed_1))
                logger.info("✅ Created: Original preprocessing")
            except Exception as e:
                logger.warning(f"⚠️ Original preprocessing failed: {e}")
            
            # Version 2: High contrast + sharpening
            try:
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                # Increase contrast dramatically
                contrast_enhanced = cv2.convertScaleAbs(gray, alpha=2.0, beta=30)
                # Apply strong sharpening
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                sharpened = cv2.filter2D(contrast_enhanced, -1, kernel)
                # Adaptive threshold
                thresh = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                
                processed_2 = Image.fromarray(thresh)
                processed_2.save(f"{debug_dir}/preprocess_contrast_{timestamp}.png")
                versions.append(("high_contrast", processed_2))
                logger.info("✅ Created: High contrast version")
            except Exception as e:
                logger.warning(f"⚠️ High contrast preprocessing failed: {e}")
            
            # Version 3: Noise reduction + morphology
            try:
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                # Strong noise reduction
                denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
                # Otsu thresholding
                _, otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                # Morphological operations
                kernel = np.ones((2,2), np.uint8)
                morphed = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
                morphed = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel)
                
                processed_3 = Image.fromarray(morphed)
                processed_3.save(f"{debug_dir}/preprocess_morphology_{timestamp}.png")
                versions.append(("morphology_enhanced", processed_3))
                logger.info("✅ Created: Morphology enhanced version")
            except Exception as e:
                logger.warning(f"⚠️ Morphology preprocessing failed: {e}")
            
            # Version 4: Edge enhancement
            try:
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                # Gaussian blur first
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)
                # Edge enhancement
                edges = cv2.Canny(blurred, 50, 150)
                # Dilate edges
                dilated_edges = cv2.dilate(edges, np.ones((2,2), np.uint8), iterations=1)
                # Combine with original
                enhanced = cv2.bitwise_or(blurred, dilated_edges)
                # Final threshold
                _, thresh = cv2.threshold(enhanced, 127, 255, cv2.THRESH_BINARY)
                
                processed_4 = Image.fromarray(thresh)
                processed_4.save(f"{debug_dir}/preprocess_edges_{timestamp}.png")
                versions.append(("edge_enhanced", processed_4))
                logger.info("✅ Created: Edge enhanced version")
            except Exception as e:
                logger.warning(f"⚠️ Edge preprocessing failed: {e}")
            
            # Version 5: Conservative approach (minimal processing)
            try:
                # Convert to RGB if needed
                if image.mode != 'RGB':
                    rgb_image = image.convert('RGB')
                else:
                    rgb_image = image
                
                # Only resize and convert to grayscale
                width, height = rgb_image.size
                if width < 1000:
                    new_width = 1000
                    new_height = int(height * (new_width / width))
                    resized = rgb_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    resized = rgb_image
                
                # Simple grayscale conversion
                gray_simple = resized.convert('L')
                gray_simple.save(f"{debug_dir}/preprocess_simple_{timestamp}.png")
                versions.append(("simple_grayscale", gray_simple))
                logger.info("✅ Created: Simple grayscale version")
            except Exception as e:
                logger.warning(f"⚠️ Simple preprocessing failed: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error creating preprocessed versions: {e}")
        
        # Ensure we have at least the original image
        if not versions:
            logger.warning("⚠️ No preprocessing succeeded, using original image")
            try:
                image.save(f"{debug_dir}/fallback_original_{timestamp}.png")
                versions.append(("fallback_original", image))
            except Exception as e:
                logger.error(f"❌ Even fallback failed: {e}")
        
        logger.info(f"📊 Created {len(versions)} preprocessed versions for analysis")
        return versions
    
    def _calculate_text_confidence(self, text: str) -> float:
        """Calculate confidence score based on text characteristics"""
        if not text or not text.strip():
            return 0.0
        
        text = text.strip()
        
        # Base score
        confidence = 0.3
        
        # Length bonus (longer text usually means better OCR)
        if len(text) > 100:
            confidence += 0.2
        elif len(text) > 50:
            confidence += 0.1
        
        # Check for typical German insurance card patterns
        patterns = [
            r'[A-ZÄÖÜ][a-zäöüß]+ [A-ZÄÖÜ][a-zäöüß]+',  # Names
            r'[A-Z]\d{9}',  # KVNR format
            r'\d{10}',      # Alternative KVNR
            r'AOK|TK|Barmer|DAK|BKK|IKK',  # Insurance companies
            r'\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4}',  # Dates
        ]
        
        pattern_matches = 0
        for pattern in patterns:
            if re.search(pattern, text):
                pattern_matches += 1
        
        # Pattern bonus
        confidence += (pattern_matches / len(patterns)) * 0.3
        
        # German character bonus
        german_chars = len(re.findall(r'[äöüÄÖÜß]', text))
        if german_chars > 0:
            confidence += min(german_chars * 0.02, 0.15)
        
        return min(confidence, 1.0)
    
    def _calculate_final_confidence(self, structured_data: Dict[str, str], raw_text: str, base_confidence: float) -> float:
        """Calculate final confidence based on extracted structured data"""
        
        data_quality = 0.0
        
        # Check quality of extracted fields
        if structured_data.get("name") and not "nicht erkannt" in structured_data["name"].lower():
            data_quality += 0.3
            
        if structured_data.get("insurance_number") and not "nicht erkannt" in structured_data["insurance_number"].lower():
            if re.match(r'^[A-Z]\d{9}$|^\d{10}$', structured_data["insurance_number"]):
                data_quality += 0.4  # High value for valid KVNR
            else:
                data_quality += 0.2
                
        if structured_data.get("insurance_company") and not "nicht erkannt" in structured_data["insurance_company"].lower():
            data_quality += 0.2
            
        if structured_data.get("birth_date") or structured_data.get("valid_until"):
            data_quality += 0.1
        
        # Combine base confidence with data quality
        final_confidence = (base_confidence * 0.6) + (data_quality * 0.4)
        
        return min(final_confidence, 0.95)  # Cap at 95%
    
    def _preprocess_for_ocr(self, image: Image) -> Image:
        """
        Preprocess image for better OCR results
        """
        try:
            logger.info(f"🖼️ Starting image preprocessing: {image.size[0]}x{image.size[1]} pixels, mode: {image.mode}")
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
                logger.info(f"🔄 Converted image to RGB mode")
            
            # ENHANCED: Resize for optimal OCR (insurance cards need higher resolution)
            width, height = image.size
            target_width = 1200  # Increased from 800 for better OCR accuracy
            if width < target_width:
                scale_factor = target_width / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"📏 Resized image from {width}x{height} to {new_width}x{new_height}")
            
            # Convert to OpenCV format for advanced preprocessing
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            logger.info(f"🔄 Converted to OpenCV format")
            
            # ENHANCED: Advanced noise reduction specifically for card text
            # Stage 1: Color denoising for camera noise
            cv_image = cv2.fastNlMeansDenoisingColored(cv_image, None, 3, 3, 7, 21)
            
            # Stage 2: Bilateral filter to smooth while preserving edges (good for text)
            cv_image = cv2.bilateralFilter(cv_image, 9, 75, 75)
            
            # Convert to grayscale for text processing
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            logger.info(f"🔄 Converted to grayscale")
            
            # ENHANCED: Adaptive histogram equalization for better contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            logger.info(f"📈 Applied CLAHE histogram equalization")
            
            # ENHANCED: Multiple preprocessing approaches - choose best one
            preprocessed_versions = []
            
            # Approach 1: Adaptive thresholding (good for varying lighting)
            try:
                adaptive_thresh = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10
                )
                preprocessed_versions.append(("adaptive_gaussian", adaptive_thresh))
                logger.info(f"✅ Created adaptive Gaussian threshold version")
            except Exception as e:
                logger.warning(f"⚠️ Adaptive thresholding failed: {e}")
            
            # Approach 2: Otsu's thresholding (good for bimodal images)
            try:
                # Apply slight Gaussian blur before Otsu
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)
                _, otsu_thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                preprocessed_versions.append(("otsu", otsu_thresh))
                logger.info(f"✅ Created Otsu threshold version")
            except Exception as e:
                logger.warning(f"⚠️ Otsu thresholding failed: {e}")
            
            # Approach 3: Enhanced contrast with manual threshold
            try:
                # Enhance contrast more aggressively
                enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=20)
                # Apply Gaussian blur
                enhanced = cv2.GaussianBlur(enhanced, (1, 1), 0)
                # Manual threshold
                _, manual_thresh = cv2.threshold(enhanced, 140, 255, cv2.THRESH_BINARY)
                preprocessed_versions.append(("manual_enhanced", manual_thresh))
                logger.info(f"✅ Created manual enhanced threshold version")
            except Exception as e:
                logger.warning(f"⚠️ Manual thresholding failed: {e}")
            
            # Choose the best preprocessing approach based on text clarity
            if preprocessed_versions:
                best_version = self._select_best_preprocessing(preprocessed_versions)
                processed = best_version[1]
                logger.info(f"🏆 Selected best preprocessing: {best_version[0]}")
            else:
                # Fallback to simple processing
                processed = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )
                logger.warning(f"⚠️ Using fallback preprocessing")
            
            # ENHANCED: Morphological operations to clean up text
            # Define different kernels for different operations
            kernel_close = np.ones((2, 2), np.uint8)  # For closing gaps in text
            kernel_open = np.ones((1, 1), np.uint8)   # For removing noise
            
            # Close small gaps in characters
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel_close)
            
            # Remove small noise
            processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel_open)
            
            # ENHANCED: Dilation and erosion to make text more solid (but preserve character boundaries)
            kernel_dilate = np.ones((1, 1), np.uint8)
            processed = cv2.dilate(processed, kernel_dilate, iterations=1)
            processed = cv2.erode(processed, kernel_dilate, iterations=1)
            
            logger.info(f"🧹 Applied morphological operations")
            
            # Convert back to PIL Image
            final_image = Image.fromarray(processed)
            
            # ENHANCED: Additional PIL-based enhancements
            # Sharpen text more aggressively
            enhancer = ImageEnhance.Sharpness(final_image)
            final_image = enhancer.enhance(2.0)  # Increased sharpening
            
            # Final contrast boost
            enhancer = ImageEnhance.Contrast(final_image)
            final_image = enhancer.enhance(1.8)  # Increased from 1.5
            
            logger.info(f"✅ Image preprocessing completed successfully")
            logger.info(f"📊 Final image: {final_image.size[0]}x{final_image.size[1]} pixels")
            
            return final_image
            
        except Exception as e:
            logger.error(f"❌ Image preprocessing error: {e}")
            logger.warning(f"🔄 Falling back to original image")
            # Return original image if preprocessing fails
            return image
    
    def _select_best_preprocessing(self, versions: list) -> tuple:
        """Select the best preprocessing version based on text clarity metrics"""
        try:
            best_score = 0
            best_version = versions[0]  # Default fallback
            
            for name, processed_img in versions:
                # Calculate a simple text clarity score
                score = self._calculate_text_clarity(processed_img)
                logger.info(f"📊 Preprocessing '{name}' score: {score:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_version = (name, processed_img)
            
            return best_version
            
        except Exception as e:
            logger.error(f"❌ Error selecting best preprocessing: {e}")
            return versions[0] if versions else ("fallback", versions[0][1])
    
    def _calculate_text_clarity(self, processed_img) -> float:
        """Calculate a text clarity score for processed image"""
        try:
            # Calculate edge strength (higher = more defined text edges)
            sobelx = cv2.Sobel(processed_img, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(processed_img, cv2.CV_64F, 0, 1, ksize=3)
            edge_strength = np.mean(np.sqrt(sobelx**2 + sobely**2))
            
            # Calculate text-to-background ratio
            text_pixels = np.sum(processed_img == 0)  # Black pixels (text)
            total_pixels = processed_img.size
            text_ratio = text_pixels / total_pixels
            
            # Optimal text ratio is around 10-30% for typical documents
            text_ratio_score = 1.0 - abs(text_ratio - 0.2) / 0.2
            text_ratio_score = max(0, text_ratio_score)
            
            # Combine metrics (edge strength weighted more heavily)
            clarity_score = (edge_strength * 0.7) + (text_ratio_score * 0.3)
            
            return clarity_score
            
        except Exception as e:
            logger.error(f"❌ Error calculating text clarity: {e}")
            return 0.0
    
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
            logger.info(f"Raw OCR text: {text[:500]}...")  # Log first 500 chars for debugging
            
            # Enhanced parsing logic for German insurance cards
            for i, line in enumerate(lines):
                line_clean = line.strip()
                line_lower = line_clean.lower()
                
                # Skip header lines
                if any(header in line_lower for header in [
                    'krankenversichertenkarte', 'versichertenkarte', 'european health',
                    'bundesrepublik', 'deutschland', 'germany', 'health insurance',
                    'krankenversicherung', 'gkv', 'pkv'
                ]):
                    continue
                
                # Name detection - enhanced patterns for German names
                if not data["name"] and self._is_likely_name(line_clean):
                    data["name"] = self._clean_name(line_clean)
                    logger.info(f"Found name: {data['name']}")
                    continue
                
                # Insurance number - German format with more patterns
                if not data["insurance_number"]:
                    # Enhanced patterns for German insurance numbers
                    ins_patterns = [
                        r'([A-Z]\d{9})',  # A123456789
                        r'(\d{10})',      # 1234567890
                        r'([A-Z]\s?\d{3}\s?\d{3}\s?\d{3})',  # A 123 456 789
                        r'(\d{4}\s?\d{3}\s?\d{3})',          # 1234 567 890
                        r'([A-Z]\d{3}\.\d{3}\.\d{3})',       # A123.456.789
                        r'(\d{3}\.\d{3}\.\d{4})'             # 123.456.7890
                    ]
                    
                    for pattern in ins_patterns:
                        ins_match = re.search(pattern, line_clean)
                        if ins_match:
                            number = ins_match.group(1).replace(' ', '').replace('.', '')
                            if self._is_valid_insurance_number(number):
                                data["insurance_number"] = number
                                logger.info(f"Found insurance number: {data['insurance_number']}")
                                break
                
                # Birth date patterns - more comprehensive
                if not data["birth_date"]:
                    birth_patterns = [
                        r'(?:geb\.?:?\s*)?(\d{1,2}\.?\d{1,2}\.?\d{2,4})',
                        r'(?:geboren:?\s*)?(\d{1,2}/\d{1,2}/\d{2,4})',
                        r'(?:birth:?\s*)?(\d{1,2}-\d{1,2}-\d{2,4})',
                        r'(\d{1,2}\.\d{1,2}\.\d{4})',  # DD.MM.YYYY
                        r'(\d{1,2}/\d{1,2}/\d{4})',   # DD/MM/YYYY
                        r'(\d{2}\.\d{2}\.\d{2})',     # DD.MM.YY
                    ]
                    for pattern in birth_patterns:
                        birth_match = re.search(pattern, line_clean, re.IGNORECASE)
                        if birth_match:
                            birth_date = birth_match.group(1)
                            if self._is_valid_date(birth_date):
                                data["birth_date"] = birth_date
                                logger.info(f"Found birth date: {data['birth_date']}")
                                break
                
                # Valid until patterns - enhanced
                if not data["valid_until"]:
                    valid_patterns = [
                        r'(?:gültig bis:?\s*)?(\d{1,2}/\d{2,4})',
                        r'(?:bis:?\s*)?(\d{1,2}\.\d{2,4})',
                        r'(?:valid until:?\s*)?(\d{1,2}-\d{2,4})',
                        r'(?:exp\.?:?\s*)?(\d{1,2}/\d{2,4})',
                        r'(\d{1,2}/\d{4})',   # MM/YYYY
                        r'(\d{1,2}\.\d{4})',  # MM.YYYY
                        r'(\d{2}/\d{2})',     # MM/YY
                        r'(\d{2}\.\d{2})'     # MM.YY
                    ]
                    for pattern in valid_patterns:
                        valid_match = re.search(pattern, line_clean, re.IGNORECASE)
                        if valid_match:
                            valid_date = valid_match.group(1)
                            data["valid_until"] = valid_date
                            logger.info(f"Found valid until: {data['valid_until']}")
                            break
                
                # Insurance company detection - enhanced
                if not data["insurance_company"] and self._is_likely_insurance_company(line_clean):
                    data["insurance_company"] = line_clean[:50]  # Limit length
                    logger.info(f"Found insurance company: {data['insurance_company']}")
                    continue
                
                # Additional search in combined lines for missed patterns
                if i < len(lines) - 1:
                    combined_line = f"{line_clean} {lines[i+1].strip()}"
                    
                    # Try name extraction from combined lines
                    if not data["name"] and self._is_likely_name(combined_line):
                        data["name"] = self._clean_name(combined_line)
                        logger.info(f"Found name in combined line: {data['name']}")
            
            # Post-processing: Fill in any missing critical data with improved fallbacks
            if not data["name"]:
                # Try to extract any capitalized words that could be names
                name_candidates = []
                for line in lines:
                    words = line.split()
                    for word in words:
                        if (word.istitle() and len(word) > 2 and 
                            re.match(r'^[A-Za-zÄÖÜäöüß\-]+$', word)):
                            name_candidates.append(word)
                
                if len(name_candidates) >= 2:
                    data["name"] = ' '.join(name_candidates[:3])  # Take first 3 candidates
                    logger.info(f"Extracted name from candidates: {data['name']}")
            
            # Validate and clean extracted data
            data = self._clean_extracted_data(data)
            
            logger.info(f"Enhanced OCR parsing result: {data}")
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
    
    def _clean_name(self, name: str) -> str:
        """Clean and format name"""
        if not name:
            return ""
        
        # Remove extra whitespace and limit length
        cleaned = re.sub(r'\s+', ' ', name.strip())[:50]
        
        # Capitalize properly (first letter of each word)
        words = cleaned.split()
        capitalized_words = []
        for word in words:
            if re.match(r'^[A-Za-zÄÖÜäöüß\-]+$', word):
                capitalized_words.append(word.capitalize())
        
        return ' '.join(capitalized_words) if capitalized_words else cleaned
    
    def _is_valid_insurance_number(self, number: str) -> bool:
        """Validate German insurance number format"""
        if not number:
            return False
        
        # Remove spaces and dots
        clean_number = number.replace(' ', '').replace('.', '')
        
        # German insurance numbers: A123456789 (letter + 9 digits) or 1234567890 (10 digits)
        return (re.match(r'^[A-Z]\d{9}$', clean_number) or 
                re.match(r'^\d{10}$', clean_number))
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Basic date validation"""
        if not date_str:
            return False
        
        # Check if it contains reasonable date components
        date_patterns = [
            r'^\d{1,2}\.\d{1,2}\.\d{2,4}$',
            r'^\d{1,2}/\d{1,2}/\d{2,4}$',
            r'^\d{1,2}-\d{1,2}-\d{2,4}$'
        ]
        
        return any(re.match(pattern, date_str) for pattern in date_patterns)
    
    def _clean_extracted_data(self, data: Dict[str, str]) -> Dict[str, str]:
        """Clean and validate extracted data"""
        cleaned = {}
        
        # Clean name
        name = data.get("name", "").strip()
        if name and len(name.split()) >= 2 and len(name) <= 50:
            cleaned["name"] = name
        else:
            cleaned["name"] = "Name nicht erkannt"
        
        # Clean insurance number
        ins_number = data.get("insurance_number", "").strip()
        if ins_number and self._is_valid_insurance_number(ins_number):
            cleaned["insurance_number"] = ins_number.replace(' ', '').replace('.', '')
        else:
            cleaned["insurance_number"] = "Nummer nicht erkannt"
        
        # Clean insurance company
        company = data.get("insurance_company", "").strip()
        if company and len(company) >= 3:
            cleaned["insurance_company"] = company[:50]
        else:
            cleaned["insurance_company"] = "Krankenkasse nicht erkannt"
        
        # Clean birth date
        birth_date = data.get("birth_date", "").strip()
        if birth_date and self._is_valid_date(birth_date):
            cleaned["birth_date"] = birth_date
        else:
            cleaned["birth_date"] = ""
        
        # Clean valid until
        valid_until = data.get("valid_until", "").strip()
        if valid_until:
            cleaned["valid_until"] = valid_until
        else:
            cleaned["valid_until"] = "Gültigkeitsdatum nicht erkannt"
        
        return cleaned
    
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
        
        # Enhanced list of German insurance company patterns
        insurance_keywords = [
            # Major public insurers (Gesetzliche Krankenkassen)
            'aok', 'tk', 'techniker', 'barmer', 'dak', 'kkh', 'hek', 
            'pronova', 'bkk', 'ikk', 'knappschaft', 'svlfg', 
            'novitas', 'salus', 'mhplus', 'viactiv', 'big',
            
            # Regional AOK branches
            'aok baden', 'aok bayern', 'aok berlin', 'aok bremen',
            'aok hessen', 'aok niedersachsen', 'aok nordost', 'aok nordwest',
            'aok plus', 'aok rheinland', 'aok sachsen', 'aok westfalen',
            
            # BKK companies
            'bkk mobil', 'bkk24', 'bkk vbu', 'bkk pfalz', 'bkk dürkopp',
            'bkk firmus', 'bkk gildemeister', 'bkk mahle', 'bkk melitta',
            'bkk publicus', 'bkk scheufelen', 'bkk textilgruppe',
            
            # IKK companies
            'ikk classic', 'ikk gesund plus', 'ikk nord', 'ikk südwest',
            
            # Private insurers (common ones)
            'continentale', 'debeka', 'signal', 'hansemerkur', 'bavaria', 
            'allianz', 'axa', 'generali', 'ergo', 'devk', 'nürnberger',
            'württembergische', 'central', 'universa', 'hallesche',
            
            # Company health funds
            'audi', 'mercedes', 'bmw', 'siemens', 'bosch', 'volkswagen',
            'lufthansa', 'deutsche bahn', 'telekom', 'post'
        ]
        
        text_lower = text.lower()
        
        # Check for exact matches or partial matches
        for keyword in insurance_keywords:
            if keyword in text_lower:
                return True
        
        # Check for generic insurance terms
        generic_terms = [
            'krankenkasse', 'krankenversicherung', 'versicherung', 
            'kasse', 'gesundheit', 'health', 'insurance'
        ]
        
        for term in generic_terms:
            if term in text_lower and len(text) > 5:
                return True
        
        return False
    
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