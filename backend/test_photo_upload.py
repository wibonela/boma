import requests
import json
from io import BytesIO
from PIL import Image

# Create a simple test image
img = Image.new('RGB', (800, 600), color='blue')
img_bytes = BytesIO()
img.save(img_bytes, format='JPEG')
img_bytes.seek(0)

# Test photo upload
property_id = "75f8cd47-8f42-42b6-86c2-c9c367530571"
url = f"http://localhost:8000/api/v1/properties/{property_id}/photos"

print(f"Testing POST {url}")
print(f"Query params: is_cover=true, display_order=0")
print()

try:
    files = {'file': ('test-image.jpg', img_bytes, 'image/jpeg')}
    params = {'is_cover': 'true', 'display_order': '0'}

    response = requests.post(url, files=files, params=params)

    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
