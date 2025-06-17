#!/usr/bin/env python3
"""
EasyOCR Model Preloader for Heroku
Pre-downloads EasyOCR models during build time to avoid timeout issues
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def preload_easyocr_models():
    """Pre-download EasyOCR models for German and English"""
    try:
        logger.info("🚀 Starting EasyOCR model preload...")
        
        # Import EasyOCR
        import easyocr
        
        # Initialize reader with German and English (this triggers model download)
        logger.info("📦 Initializing EasyOCR Reader with German and English...")
        reader = easyocr.Reader(['de', 'en'], gpu=False, verbose=True)
        
        # Test with a simple image to ensure everything works
        import numpy as np
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        logger.info("🧪 Testing OCR with sample image...")
        result = reader.readtext(test_image)
        
        logger.info("✅ EasyOCR models preloaded successfully!")
        logger.info(f"✅ Test result: {len(result)} text regions detected")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to preload EasyOCR models: {e}")
        return False

def main():
    """Main preload function"""
    logger.info("🎯 EasyOCR Model Preloader Starting...")
    
    # Check if we're in build environment
    build_env = os.environ.get('BUILD_TIME', 'false').lower() == 'true'
    
    if build_env:
        logger.info("🏗️ Build-time detected - preloading models...")
    else:
        logger.info("🚀 Runtime preload initiated...")
    
    success = preload_easyocr_models()
    
    if success:
        logger.info("🎉 Model preload completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Model preload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 