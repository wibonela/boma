"""
Simple Cloudinary setup checker - no dependencies required except standard library.
"""

import os
from pathlib import Path

print("=" * 70)
print("BOMA CLOUDINARY INTEGRATION - FILE STRUCTURE CHECK")
print("=" * 70)
print()

backend_dir = Path(__file__).parent

# Check 1: Environment file
print("✓ CHECK 1: Environment File (.env)")
print("-" * 70)
env_file = backend_dir / ".env"
if env_file.exists():
    print(f"  ✅ .env file exists: {env_file}")

    # Read and check for Cloudinary variables
    with open(env_file, 'r') as f:
        env_content = f.read()

    cloudinary_vars = [
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_API_KEY",
        "CLOUDINARY_API_SECRET",
        "CLOUDINARY_FOLDER"
    ]

    for var in cloudinary_vars:
        if var in env_content and f"{var}=" in env_content:
            # Extract value
            for line in env_content.split('\n'):
                if line.strip().startswith(f"{var}="):
                    value = line.split('=', 1)[1].strip()
                    if value and value != "your-" and not value.startswith("CLOUDINARY_URL"):
                        print(f"  ✅ {var} is set")
                    else:
                        print(f"  ❌ {var} is empty or placeholder")
                    break
        else:
            print(f"  ❌ {var} not found in .env")
else:
    print(f"  ❌ .env file not found at {env_file}")
    print("  Create it from .env.example")

print()

# Check 2: Cloudinary service file
print("✓ CHECK 2: Cloudinary Service File")
print("-" * 70)
service_file = backend_dir / "app" / "services" / "cloudinary_service.py"
if service_file.exists():
    print(f"  ✅ cloudinary_service.py exists")

    # Check for key functions
    with open(service_file, 'r') as f:
        service_content = f.read()

    functions = [
        "upload_property_image",
        "delete_image",
        "_generate_thumbnail_url",
        "extract_public_id_from_url"
    ]

    for func in functions:
        if f"def {func}" in service_content:
            print(f"  ✅ Function '{func}' defined")
        else:
            print(f"  ❌ Function '{func}' missing")
else:
    print(f"  ❌ cloudinary_service.py not found")

print()

# Check 3: Property endpoints file
print("✓ CHECK 3: Property Endpoints File")
print("-" * 70)
endpoints_file = backend_dir / "app" / "api" / "v1" / "endpoints" / "properties.py"
if endpoints_file.exists():
    print(f"  ✅ properties.py exists")

    with open(endpoints_file, 'r') as f:
        endpoints_content = f.read()

    photo_endpoints = [
        "upload_property_photo",
        "delete_property_photo",
        "update_property_photo",
        "reorder_property_photos"
    ]

    for endpoint in photo_endpoints:
        if f"async def {endpoint}" in endpoints_content:
            print(f"  ✅ Endpoint '{endpoint}' defined")
        else:
            print(f"  ❌ Endpoint '{endpoint}' missing")

    # Check for cloudinary_service import
    if "from app.services.cloudinary_service import cloudinary_service" in endpoints_content:
        print(f"  ✅ cloudinary_service imported")
    else:
        print(f"  ⚠️  cloudinary_service import not found")

else:
    print(f"  ❌ properties.py not found")

print()

# Check 4: Property schemas
print("✓ CHECK 4: Property Schemas File")
print("-" * 70)
schemas_file = backend_dir / "app" / "schemas" / "property.py"
if schemas_file.exists():
    print(f"  ✅ property.py (schemas) exists")

    with open(schemas_file, 'r') as f:
        schemas_content = f.read()

    photo_schemas = [
        "PropertyPhotoBase",
        "PropertyPhotoResponse",
        "PropertyPhotoUpdate",
        "PropertyPhotoReorder"
    ]

    for schema in photo_schemas:
        if f"class {schema}" in schemas_content:
            print(f"  ✅ Schema '{schema}' defined")
        else:
            print(f"  ❌ Schema '{schema}' missing")

    # Check if PropertyResponse includes photos
    if "photos:" in schemas_content and "PropertyPhotoResponse" in schemas_content:
        print(f"  ✅ PropertyResponse includes photos field")
    else:
        print(f"  ⚠️  PropertyResponse may not include photos field")

else:
    print(f"  ❌ property.py (schemas) not found")

print()

# Check 5: Property models
print("✓ CHECK 5: Property Models File")
print("-" * 70)
models_file = backend_dir / "app" / "models" / "property.py"
if models_file.exists():
    print(f"  ✅ property.py (models) exists")

    with open(models_file, 'r') as f:
        models_content = f.read()

    if "class PropertyPhoto" in models_content:
        print(f"  ✅ PropertyPhoto model defined")

        # Check key fields
        fields = ["photo_url", "thumbnail_url", "display_order", "is_cover", "caption"]
        for field in fields:
            if field in models_content:
                print(f"  ✅ Field '{field}' present")
            else:
                print(f"  ❌ Field '{field}' missing")
    else:
        print(f"  ❌ PropertyPhoto model not found")
else:
    print(f"  ❌ property.py (models) not found")

print()

# Check 6: API Router
print("✓ CHECK 6: API Router Configuration")
print("-" * 70)
api_init_file = backend_dir / "app" / "api" / "v1" / "__init__.py"
if api_init_file.exists():
    print(f"  ✅ api/v1/__init__.py exists")

    with open(api_init_file, 'r') as f:
        api_content = f.read()

    if "from app.api.v1.endpoints import" in api_content and "properties" in api_content:
        print(f"  ✅ Properties endpoints imported")
    else:
        print(f"  ⚠️  Properties endpoints may not be imported")

    if "api_router.include_router(properties.router)" in api_content:
        print(f"  ✅ Properties router included in API")
    else:
        print(f"  ⚠️  Properties router may not be included")
else:
    print(f"  ❌ api/v1/__init__.py not found")

print()

# Check 7: Alembic migration
print("✓ CHECK 7: Database Migration")
print("-" * 70)
versions_dir = backend_dir / "alembic" / "versions"
if versions_dir.exists():
    migration_files = list(versions_dir.glob("*.py"))
    if migration_files:
        print(f"  ✅ Found {len(migration_files)} migration file(s)")

        # Check if any migration includes property_photos
        has_property_photos = False
        for migration_file in migration_files:
            with open(migration_file, 'r') as f:
                if "property_photos" in f.read():
                    has_property_photos = True
                    print(f"  ✅ property_photos table in migration: {migration_file.name}")
                    break

        if not has_property_photos:
            print(f"  ⚠️  property_photos table not found in migrations")
    else:
        print(f"  ⚠️  No migration files found")
else:
    print(f"  ⚠️  Alembic versions directory not found")

print()

# Check 8: Requirements
print("✓ CHECK 8: Requirements File")
print("-" * 70)
requirements_file = backend_dir / "requirements.txt"
if requirements_file.exists():
    print(f"  ✅ requirements.txt exists")

    with open(requirements_file, 'r') as f:
        requirements = f.read()

    if "cloudinary" in requirements:
        print(f"  ✅ cloudinary package in requirements.txt")
    else:
        print(f"  ❌ cloudinary package not in requirements.txt")
else:
    print(f"  ❌ requirements.txt not found")

print()

# Check 9: Mobile API config
print("✓ CHECK 9: Mobile API Configuration")
print("-" * 70)
mobile_config = Path(backend_dir).parent / "mobile" / "src" / "api" / "config.ts"
if mobile_config.exists():
    print(f"  ✅ Mobile API config exists")

    with open(mobile_config, 'r') as f:
        config_content = f.read()

    mobile_endpoints = [
        "UPLOAD_PHOTO",
        "DELETE_PHOTO",
        "UPDATE_PHOTO",
        "REORDER_PHOTOS"
    ]

    for endpoint in mobile_endpoints:
        if endpoint in config_content:
            print(f"  ✅ Endpoint '{endpoint}' configured")
        else:
            print(f"  ❌ Endpoint '{endpoint}' missing")
else:
    print(f"  ⚠️  Mobile API config not found (expected if mobile not set up)")

print()

# Check 10: Mobile property service
print("✓ CHECK 10: Mobile Property Service")
print("-" * 70)
mobile_service = Path(backend_dir).parent / "mobile" / "src" / "api" / "services" / "propertyService.ts"
if mobile_service.exists():
    print(f"  ✅ Mobile property service exists")

    with open(mobile_service, 'r') as f:
        service_content = f.read()

    mobile_functions = [
        "uploadPropertyPhoto",
        "deletePropertyPhoto",
        "updatePropertyPhoto",
        "reorderPropertyPhotos"
    ]

    for func in mobile_functions:
        if func in service_content:
            print(f"  ✅ Function '{func}' defined")
        else:
            print(f"  ❌ Function '{func}' missing")
else:
    print(f"  ⚠️  Mobile property service not found")

print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print("✅ File structure check complete!")
print()
print("To complete setup:")
print("1. Ensure all dependencies are installed:")
print("   cd backend && pip install -r requirements.txt")
print()
print("2. Run database migrations:")
print("   cd backend && alembic upgrade head")
print()
print("3. Start the backend server:")
print("   cd backend && uvicorn app.main:app --reload")
print()
print("4. Test the upload endpoint:")
print("   curl -X POST http://localhost:8000/api/v1/properties/{id}/photos \\")
print("     -F 'file=@/path/to/image.jpg'")
print()
