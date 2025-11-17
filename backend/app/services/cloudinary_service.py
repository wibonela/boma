"""
Cloudinary service for image upload and management.

This module handles all Cloudinary operations including:
- Image uploads with automatic optimization
- Thumbnail generation
- Image deletion
- URL generation with transformations
"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url
from typing import Optional, Dict, Any
import logging
from uuid import UUID
from pathlib import Path
import io

from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudinaryService:
    """Service for managing image uploads and transformations via Cloudinary."""

    def __init__(self):
        """Initialize Cloudinary configuration."""
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True  # Always use HTTPS
        )
        logger.info(f"Cloudinary initialized with cloud: {settings.CLOUDINARY_CLOUD_NAME}")

    def upload_property_image(
        self,
        file_content: bytes,
        property_id: UUID,
        filename: str,
        photo_id: UUID
    ) -> Dict[str, str]:
        """
        Upload a property image to Cloudinary.

        Args:
            file_content: Raw image bytes
            property_id: UUID of the property
            filename: Original filename
            photo_id: UUID for this specific photo

        Returns:
            Dict containing:
                - photo_url: Full resolution image URL
                - thumbnail_url: Thumbnail image URL
                - public_id: Cloudinary public ID for deletion

        Raises:
            Exception: If upload fails
        """
        try:
            # Generate folder path: boma/properties/property-{uuid}
            folder = f"{settings.CLOUDINARY_FOLDER}/property-{str(property_id)}"

            # Generate public_id: photo-{uuid}
            public_id = f"photo-{str(photo_id)}"

            # Get file extension from original filename
            file_extension = Path(filename).suffix.lower()
            if not file_extension:
                file_extension = ".jpg"  # Default to jpg

            # Upload to Cloudinary with optimizations
            upload_result = cloudinary.uploader.upload(
                io.BytesIO(file_content),
                folder=folder,
                public_id=public_id,
                resource_type="image",
                format=file_extension.lstrip('.'),
                transformation=[
                    {
                        'quality': 'auto:good',  # Automatic quality optimization
                        'fetch_format': 'auto'    # Automatic format selection (WebP where supported)
                    }
                ],
                # Additional metadata
                context={
                    'property_id': str(property_id),
                    'photo_id': str(photo_id),
                    'original_filename': filename
                }
            )

            # Get the full photo URL
            photo_url = upload_result['secure_url']

            # Generate thumbnail URL with transformations
            thumbnail_url = self._generate_thumbnail_url(
                upload_result['public_id'],
                width=400,
                height=300
            )

            logger.info(
                f"Successfully uploaded image for property {property_id}, "
                f"photo {photo_id}: {photo_url}"
            )

            return {
                'photo_url': photo_url,
                'thumbnail_url': thumbnail_url,
                'public_id': upload_result['public_id']
            }

        except Exception as e:
            logger.error(f"Failed to upload image to Cloudinary: {str(e)}")
            raise Exception(f"Image upload failed: {str(e)}")

    def _generate_thumbnail_url(
        self,
        public_id: str,
        width: int = 400,
        height: int = 300,
        crop: str = "fill"
    ) -> str:
        """
        Generate a thumbnail URL with specific transformations.

        Args:
            public_id: Cloudinary public ID
            width: Thumbnail width in pixels
            height: Thumbnail height in pixels
            crop: Crop mode (fill, fit, scale, etc.)

        Returns:
            Thumbnail URL string
        """
        url, _ = cloudinary_url(
            public_id,
            transformation=[
                {
                    'width': width,
                    'height': height,
                    'crop': crop,
                    'quality': 'auto:good',
                    'fetch_format': 'auto'
                }
            ],
            secure=True
        )
        return url

    def delete_image(self, public_id: str) -> bool:
        """
        Delete an image from Cloudinary.

        Args:
            public_id: Cloudinary public ID (includes folder path)

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            result = cloudinary.uploader.destroy(public_id)

            if result.get('result') == 'ok':
                logger.info(f"Successfully deleted image: {public_id}")
                return True
            else:
                logger.warning(f"Image deletion returned non-OK result: {result}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete image {public_id}: {str(e)}")
            return False

    def get_image_info(self, public_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an image.

        Args:
            public_id: Cloudinary public ID

        Returns:
            Image information dict or None if not found
        """
        try:
            result = cloudinary.api.resource(public_id)
            return result
        except cloudinary.exceptions.NotFound:
            logger.warning(f"Image not found: {public_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get image info for {public_id}: {str(e)}")
            return None

    def extract_public_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract Cloudinary public_id from a full URL.

        Args:
            url: Full Cloudinary URL

        Returns:
            Public ID string or None if extraction fails

        Example:
            Input: "https://res.cloudinary.com/demo/image/upload/v1234/boma/properties/property-123/photo-456.jpg"
            Output: "boma/properties/property-123/photo-456"
        """
        try:
            # Split by /upload/ to get the part after it
            parts = url.split('/upload/')
            if len(parts) < 2:
                return None

            # Get everything after /upload/
            after_upload = parts[1]

            # Remove version prefix (v1234567/) if present
            if after_upload.startswith('v') and '/' in after_upload:
                version_parts = after_upload.split('/', 1)
                if version_parts[0][1:].isdigit():
                    after_upload = version_parts[1]

            # Remove file extension
            public_id = Path(after_upload).with_suffix('').as_posix()

            return public_id

        except Exception as e:
            logger.error(f"Failed to extract public_id from URL {url}: {str(e)}")
            return None

    def generate_signed_upload_params(
        self,
        property_id: UUID,
        photo_id: UUID
    ) -> Dict[str, Any]:
        """
        Generate signed upload parameters for direct client uploads.

        This can be used in the future for direct uploads from mobile to Cloudinary,
        bypassing the backend. Currently not used but prepared for future optimization.

        Args:
            property_id: UUID of the property
            photo_id: UUID for this specific photo

        Returns:
            Dict with signature, timestamp, and other upload parameters
        """
        folder = f"{settings.CLOUDINARY_FOLDER}/property-{str(property_id)}"
        public_id = f"photo-{str(photo_id)}"

        timestamp = cloudinary.utils.now()

        params_to_sign = {
            'timestamp': timestamp,
            'folder': folder,
            'public_id': public_id,
            'transformation': 'quality_auto:good,fetch_format_auto'
        }

        signature = cloudinary.utils.api_sign_request(
            params_to_sign,
            settings.CLOUDINARY_API_SECRET
        )

        return {
            **params_to_sign,
            'signature': signature,
            'api_key': settings.CLOUDINARY_API_KEY,
            'cloud_name': settings.CLOUDINARY_CLOUD_NAME
        }


# Global instance
cloudinary_service = CloudinaryService()
