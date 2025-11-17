import requests
import json

# Test property update
property_id = "75f8cd47-8f42-42b6-86c2-c9c367530571"
url = f"http://localhost:8000/api/v1/properties/{property_id}"

data = {
    "title": "Updated Beautiful Apartment",
    "description": "An updated beautiful test property in Dar es Salaam with amazing views"
}

print(f"Testing PUT {url}")
print(f"Data: {json.dumps(data, indent=2)}")
print()

try:
    response = requests.put(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
