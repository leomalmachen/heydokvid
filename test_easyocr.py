#!/usr/bin/env python3
"""
Test Script für EasyOCR Insurance Card Service
Lokaler Test der neuen EasyOCR-Implementierung
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.insurance_card_service import InsuranceCardService
from database import SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_easyocr_installation():
    """Test if EasyOCR is properly installed and working"""
    try:
        import easyocr
        print("✅ EasyOCR import successful")
        
        # Test reader initialization
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        print("✅ EasyOCR Reader initialization successful")
        
        return True
    except Exception as e:
        print(f"❌ EasyOCR installation test failed: {e}")
        return False

def test_service_initialization():
    """Test InsuranceCardService initialization"""
    try:
        db = SessionLocal()
        service = InsuranceCardService(db)
        print("✅ InsuranceCardService initialization successful")
        
        if service.reader:
            print("✅ EasyOCR reader successfully initialized in service")
        else:
            print("❌ EasyOCR reader failed to initialize in service")
            return False
            
        db.close()
        return True
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False

def test_with_sample_image():
    """Test OCR with a sample image if available"""
    try:
        # Look for sample images in uploads directory
        uploads_dir = project_root / "uploads"
        
        if not uploads_dir.exists():
            print("ℹ️  No uploads directory found - skipping image test")
            return True
            
        # Find any image files
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(uploads_dir.glob(ext))
        
        if not image_files:
            print("ℹ️  No test images found - skipping image test")
            return True
            
        # Test with first found image
        test_image = image_files[0]
        print(f"🔍 Testing with image: {test_image.name}")
        
        db = SessionLocal()
        service = InsuranceCardService(db)
        
        with open(test_image, 'rb') as f:
            image_bytes = f.read()
        
        result = service.extract_card_data(image_bytes)
        
        print("📋 OCR Test Results:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Confidence: {result.get('confidence', 0):.3f}")
        print(f"   Approach: {result.get('approach_used', 'N/A')}")
        
        if result.get('success'):
            data = result.get('data', {})
            print("   Extracted Data:")
            for key, value in data.items():
                if value:
                    print(f"     {key}: {value}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Image test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting EasyOCR Implementation Tests\n")
    
    tests = [
        ("EasyOCR Installation", test_easyocr_installation),
        ("Service Initialization", test_service_initialization),
        ("Sample Image Processing", test_with_sample_image),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name} passed\n")
            else:
                print(f"❌ {test_name} failed\n")
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}\n")
            results.append((test_name, False))
    
    # Summary
    print("📊 Test Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! EasyOCR implementation is ready.")
    else:
        print("⚠️  Some tests failed. Check the logs above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 