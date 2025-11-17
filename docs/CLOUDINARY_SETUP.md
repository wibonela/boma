# Cloudinary Integration Setup Guide

## Getting Your Cloudinary Credentials

Follow these steps to obtain the required credentials for Cloudinary integration:

### Step 1: Create or Log In to Cloudinary Account

1. Go to [https://cloudinary.com](https://cloudinary.com)
2. If you don't have an account:
   - Click "Sign Up"
   - Choose the free plan (generous limits for development)
   - Complete the registration
3. If you already have an account, click "Log In"

### Step 2: Access Your Dashboard

1. After logging in, you'll be redirected to your **Dashboard**
2. The URL will look like: `https://console.cloudinary.com/console/<your-cloud-name>/getting-started`

### Step 3: Locate Your Credentials

On the Dashboard, you'll see a section called **"Product Environment Credentials"** or **"Account Details"**:

```
Cloud name: your-cloud-name
API Key: 123456789012345
API Secret: AbCdEfGhIjKlMnOpQrStUvWxYz123
```

**Important:** Click the "eye" icon next to API Secret to reveal it.

### Step 4: Copy Your Credentials

You need these three values:

| Credential | Where to Find | Example |
|------------|---------------|---------|
| **Cloud Name** | Top of dashboard, under "Product Environment Credentials" | `dar5w44sh` |
| **API Key** | Listed directly on dashboard | `777444329175487` |
| **API Secret** | Click eye icon to reveal | `vGEXAAcLUs3jccNNslavT58-Tls` |

### Step 5: Update Your Backend .env File

1. Open `backend/.env` (create it from `.env.example` if it doesn't exist)
2. Add or update these lines:

```bash
# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
CLOUDINARY_FOLDER=boma/properties
```

**Example:**
```bash
CLOUDINARY_CLOUD_NAME=dar5w44sh
CLOUDINARY_API_KEY=777444329175487
CLOUDINARY_API_SECRET=vGEXAAcLUs3jccNNslavT58-Tls
CLOUDINARY_FOLDER=boma/properties
```

### Alternative: Using Cloudinary URL (Optional)

Cloudinary also provides a single environment variable format:

```bash
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

**Example:**
```bash
CLOUDINARY_URL=cloudinary://777444329175487:vGEXAAcLUs3jccNNslavT58-Tls@dar5w44sh
```

However, we use the separated format for clarity and easier configuration management.

## Cloudinary Dashboard Features

### Useful Dashboard Sections:

1. **Media Library** - View all uploaded images
   - Access at: Console → Media Library
   - Here you can browse, search, and manage uploaded images

2. **Upload Presets** - Configure default upload settings
   - Access at: Settings → Upload
   - Useful for setting default transformations

3. **Transformations** - View transformation usage
   - Access at: Reports → Transformations
   - Monitor which image transformations you're using

4. **Usage** - Monitor your plan limits
   - Access at: Reports → Usage
   - Track bandwidth, storage, and transformations

## Folder Structure in Cloudinary

When you upload images, they'll be organized as:

```
boma/
  └── properties/
      ├── property-{uuid}/
      │   ├── photo-{uuid}_original.jpg
      │   └── photo-{uuid}_thumbnail.jpg
      └── property-{uuid}/
          └── ...
```

This keeps your media organized by property.

## Security Best Practices

1. **Never commit .env to Git** - It's already in .gitignore
2. **Rotate API secrets regularly** - Do this from Settings → Security
3. **Use signed uploads in production** - Prevents unauthorized uploads
4. **Set up allowed formats** - Limit to jpg, png, webp only
5. **Configure rate limits** - Prevent abuse

## Testing Your Connection

After setting up credentials, you can test the connection with this Python code:

```python
import cloudinary
from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

# Test upload
result = cloudinary.uploader.upload(
    "test.jpg",
    folder=settings.CLOUDINARY_FOLDER
)
print(f"Upload successful: {result['secure_url']}")
```

## Common Issues and Solutions

### Issue: "Invalid cloud_name"
**Solution:** Double-check your cloud name in the dashboard. It's case-sensitive.

### Issue: "Invalid API credentials"
**Solution:** Make sure you copied the API Secret correctly (click the eye icon to reveal it).

### Issue: "Upload failed: resource_not_found"
**Solution:** Check that your folder path doesn't have leading/trailing slashes.

### Issue: Images not showing in Media Library
**Solution:** Make sure you're looking in the correct folder (`boma/properties`).

## Next Steps

After setting up credentials:
1. Restart your backend server to load new environment variables
2. Test photo upload from the EditProperty screen in the mobile app
3. Check Media Library to confirm images are uploaded
4. Verify thumbnails are generated correctly

## Support Resources

- Cloudinary Documentation: https://cloudinary.com/documentation
- Upload API Reference: https://cloudinary.com/documentation/image_upload_api_reference
- Python SDK: https://cloudinary.com/documentation/django_integration
- Support: https://support.cloudinary.com

---

**Created:** 2025-11-15
**Last Updated:** 2025-11-15
