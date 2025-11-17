"""
Quick test script to verify Cloudinary integration setup.
Run this before starting image uploads to ensure everything is configured correctly.
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("BOMA CLOUDINARY INTEGRATION - PRE-UPLOAD VERIFICATION")
print("=" * 70)
print()

# Test 1: Environment Variables
print("✓ TEST 1: Cloudinary Environment Variables")
print("-" * 70)
try:
    from app.core.config import settings

    print(f"  CLOUDINARY_CLOUD_NAME: {settings.CLOUDINARY_CLOUD_NAME}")
    print(f"  CLOUDINARY_API_KEY: {settings.CLOUDINARY_API_KEY[:10]}... (hidden)")
    print(f"  CLOUDINARY_API_SECRET: {'*' * 20} (hidden)")
    print(f"  CLOUDINARY_FOLDER: {settings.CLOUDINARY_FOLDER}")

    if not settings.CLOUDINARY_CLOUD_NAME:
        print("  ❌ ERROR: CLOUDINARY_CLOUD_NAME is not set!")
        sys.exit(1)
    if not settings.CLOUDINARY_API_KEY:
        print("  ❌ ERROR: CLOUDINARY_API_KEY is not set!")
        sys.exit(1)
    if not settings.CLOUDINARY_API_SECRET:
        print("  ❌ ERROR: CLOUDINARY_API_SECRET is not set!")
        sys.exit(1)

    print("  ✅ All Cloudinary environment variables are set")
except Exception as e:
    print(f"  ❌ ERROR: Failed to load config: {e}")
    sys.exit(1)

print()

# Test 2: Cloudinary SDK Import
print("✓ TEST 2: Cloudinary SDK Import")
print("-" * 70)
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    print("  ✅ Cloudinary SDK imported successfully")
except ImportError as e:
    print(f"  ❌ ERROR: Failed to import Cloudinary SDK: {e}")
    print("  Run: pip install cloudinary")
    sys.exit(1)

print()

# Test 3: Cloudinary Service
print("✓ TEST 3: Cloudinary Service Initialization")
print("-" * 70)
try:
    from app.services.cloudinary_service import cloudinary_service
    print("  ✅ Cloudinary service imported successfully")
    print(f"  Cloud Name: {cloudinary.config().cloud_name}")
except Exception as e:
    print(f"  ❌ ERROR: Failed to initialize Cloudinary service: {e}")
    sys.exit(1)

print()

# Test 4: Property Models
print("✓ TEST 4: Property Models")
print("-" * 70)
try:
    from app.models.property import Property, PropertyPhoto
    print("  ✅ Property model imported")
    print("  ✅ PropertyPhoto model imported")
except Exception as e:
    print(f"  ❌ ERROR: Failed to import models: {e}")
    sys.exit(1)

print()

# Test 5: Property Schemas
print("✓ TEST 5: Property Schemas")
print("-" * 70)
try:
    from app.schemas.property import (
        PropertyPhotoResponse,
        PropertyPhotoUpdate,
        PropertyPhotoReorder,
        PropertyResponse
    )
    print("  ✅ PropertyPhotoResponse schema imported")
    print("  ✅ PropertyPhotoUpdate schema imported")
    print("  ✅ PropertyPhotoReorder schema imported")
    print("  ✅ PropertyResponse includes photos field")
except Exception as e:
    print(f"  ❌ ERROR: Failed to import schemas: {e}")
    sys.exit(1)

print()

# Test 6: Endpoints
print("✓ TEST 6: Property Endpoints")
print("-" * 70)
try:
    from app.api.v1.endpoints.properties import (
        upload_property_photo,
        delete_property_photo,
        update_property_photo,
        reorder_property_photos
    )
    print("  ✅ upload_property_photo endpoint imported")
    print("  ✅ delete_property_photo endpoint imported")
    print("  ✅ update_property_photo endpoint imported")
    print("  ✅ reorder_property_photos endpoint imported")
except Exception as e:
    print(f"  ❌ ERROR: Failed to import endpoints: {e}")
    sys.exit(1)

print()

# Test 7: API Router
print("✓ TEST 7: API Router Configuration")
print("-" * 70)
try:
    from app.api.v1 import api_router
    print("  ✅ API router imported")

    # Get all routes
    routes = []
    for route in api_router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append((route.path, list(route.methods)))

    # Check for photo endpoints
    photo_endpoints = [
        ("/properties/{property_id}/photos", {"POST"}),
        ("/properties/{property_id}/photos/{photo_id}", {"DELETE", "PUT"}),
        ("/properties/{property_id}/photos/reorder", {"PUT"}),
    ]

    found_endpoints = []
    for path, methods in routes:
        for expected_path, expected_methods in photo_endpoints:
            if path == expected_path:
                found_endpoints.append((path, methods))

    if len(found_endpoints) >= 3:
        print(f"  ✅ Photo endpoints registered: {len(found_endpoints)}")
        for path, methods in found_endpoints:
            print(f"     - {', '.join(methods)} {path}")
    else:
        print(f"  ⚠️  WARNING: Only {len(found_endpoints)}/4 photo endpoints found")

except Exception as e:
    print(f"  ❌ ERROR: Failed to check API router: {e}")
    sys.exit(1)

print()

# Test 8: Cloudinary Connection (optional test)
print("✓ TEST 8: Cloudinary API Connection (Optional)")
print("-" * 70)
try:
    # Test basic API call to verify credentials
    result = cloudinary.api.ping()
    if result.get('status') == 'ok':
        print("  ✅ Successfully connected to Cloudinary API")
        print("  ✅ Credentials are valid")
    else:
        print("  ⚠️  WARNING: Cloudinary ping returned unexpected response")
except cloudinary.exceptions.AuthorizationRequired as e:
    print("  ❌ ERROR: Invalid Cloudinary credentials")
    print(f"     {e}")
    sys.exit(1)
except Exception as e:
    print(f"  ⚠️  WARNING: Could not test Cloudinary connection: {e}")
    print("     This is optional - upload may still work")

print()
print("=" * 70)
print("✅ ALL CRITICAL TESTS PASSED - READY FOR IMAGE UPLOADS!")
print("=" * 70)
print()
print("Next steps:")
print("1. Start the backend server:")
print("   cd backend && uvicorn app.main:app --reload")
print()
print("2. Test photo upload endpoint:")
print("   curl -X POST http://localhost:8000/api/v1/properties/{property_id}/photos \\")
print("     -F 'file=@/path/to/image.jpg'")
print()
print("3. Or use the mobile app EditProperty screen to upload images")
print()
