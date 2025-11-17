"""
Local file storage service for image and document management.

This module handles all file operations including:
- Image uploads with automatic optimization
- Thumbnail generation
- File deletion
- Secure file serving
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import UUID
import logging
from PIL import Image
import io

from app.core.config import settings

logger = logging.getLogger(__name__)


class FileStorageService:
    """Service for managing file uploads and storage locally."""

    def __init__(self):
        """Initialize file storage and ensure directories exist."""
        self.base_upload_dir = Path(settings.UPLOAD_DIR)
        self.properties_dir = self.base_upload_dir / "properties"
        self.documents_dir = self.base_upload_dir / "documents"
        self.profiles_dir = self.base_upload_dir / "profiles"

        # Create directories if they don't exist
        self._ensure_directories()

        logger.info(f"File storage initialized at: {self.base_upload_dir.absolute()}")

    def _ensure_directories(self):
        """Ensure all required directories exist."""
        for directory in [self.properties_dir, self.documents_dir, self.profiles_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ensured: {directory}")

    def upload_property_image(
        self,
        file_content: bytes,
        property_id: UUID,
        filename: str,
        photo_id: UUID
    ) -> Dict[str, str]:
        """
        Upload a property image to local storage.

        Args:
            file_content: Raw image bytes
            property_id: UUID of the property
            filename: Original filename
            photo_id: UUID for this specific photo

        Returns:
            Dict containing:
                - photo_url: Full resolution image URL path
                - thumbnail_url: Thumbnail image URL path
                - file_path: Server file path for deletion

        Raises:
            Exception: If upload fails
        """
        try:
            # Create property-specific folder
            property_folder = self.properties_dir / f"property-{str(property_id)}"
            property_folder.mkdir(parents=True, exist_ok=True)

            # Generate filenames
            file_extension = Path(filename).suffix.lower() or ".jpg"
            photo_filename = f"photo-{str(photo_id)}{file_extension}"
            thumbnail_filename = f"photo-{str(photo_id)}_thumb{file_extension}"

            # Full paths
            photo_path = property_folder / photo_filename
            thumbnail_path = property_folder / thumbnail_filename

            # Save original image with optimization
            image = Image.open(io.BytesIO(file_content))

            # Convert RGBA to RGB if necessary (for JPEG)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background

            # Resize if too large (max 2000px on longest side)
            max_size = 2000
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Save full image with good quality
            image.save(
                photo_path,
                format='JPEG',
                quality=85,
                optimize=True
            )

            # Generate and save thumbnail (400x300)
            thumbnail = image.copy()
            thumbnail.thumbnail((400, 300), Image.Resampling.LANCZOS)
            thumbnail.save(
                thumbnail_path,
                format='JPEG',
                quality=80,
                optimize=True
            )

            # Generate URL paths (relative to static serving)
            photo_url = f"{settings.STATIC_URL}/properties/property-{str(property_id)}/{photo_filename}"
            thumbnail_url = f"{settings.STATIC_URL}/properties/property-{str(property_id)}/{thumbnail_filename}"

            logger.info(
                f"Successfully uploaded image for property {property_id}, "
                f"photo {photo_id}: {photo_path}"
            )

            return {
                'photo_url': photo_url,
                'thumbnail_url': thumbnail_url,
                'file_path': str(photo_path.relative_to(self.base_upload_dir))
            }

        except Exception as e:
            logger.error(f"Failed to upload image to local storage: {str(e)}")
            raise Exception(f"Image upload failed: {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from local storage.

        Args:
            file_path: Relative file path from upload directory

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            full_path = self.base_upload_dir / file_path

            if full_path.exists() and full_path.is_file():
                full_path.unlink()
                logger.info(f"Successfully deleted file: {file_path}")

                # Also delete thumbnail if it exists
                if "_thumb" not in str(file_path):
                    thumb_path = full_path.parent / f"{full_path.stem}_thumb{full_path.suffix}"
                    if thumb_path.exists():
                        thumb_path.unlink()
                        logger.info(f"Deleted thumbnail: {thumb_path}")

                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False

    def upload_document(
        self,
        file_content: bytes,
        user_id: UUID,
        filename: str,
        document_id: UUID,
        document_type: str = "kyc"
    ) -> Dict[str, str]:
        """
        Upload a document (PDF, image) to local storage.

        Args:
            file_content: Raw file bytes
            user_id: UUID of the user
            filename: Original filename
            document_id: UUID for this specific document
            document_type: Type of document (kyc, contract, etc.)

        Returns:
            Dict containing:
                - document_url: Document URL path
                - file_path: Server file path for deletion
        """
        try:
            # Create user-specific folder
            user_folder = self.documents_dir / document_type / f"user-{str(user_id)}"
            user_folder.mkdir(parents=True, exist_ok=True)

            # Generate filename
            file_extension = Path(filename).suffix.lower() or ".pdf"
            document_filename = f"doc-{str(document_id)}{file_extension}"

            # Full path
            document_path = user_folder / document_filename

            # Save document
            with open(document_path, 'wb') as f:
                f.write(file_content)

            # Generate URL path
            document_url = f"{settings.STATIC_URL}/documents/{document_type}/user-{str(user_id)}/{document_filename}"

            logger.info(
                f"Successfully uploaded document for user {user_id}, "
                f"document {document_id}: {document_path}"
            )

            return {
                'document_url': document_url,
                'file_path': str(document_path.relative_to(self.base_upload_dir))
            }

        except Exception as e:
            logger.error(f"Failed to upload document to local storage: {str(e)}")
            raise Exception(f"Document upload failed: {str(e)}")

    def upload_profile_photo(
        self,
        file_content: bytes,
        user_id: UUID,
        filename: str
    ) -> Dict[str, str]:
        """
        Upload a profile photo to local storage.

        Args:
            file_content: Raw image bytes
            user_id: UUID of the user
            filename: Original filename

        Returns:
            Dict containing:
                - photo_url: Profile photo URL path
                - thumbnail_url: Thumbnail URL path
                - file_path: Server file path for deletion
        """
        try:
            # Create user-specific folder
            user_folder = self.profiles_dir / f"user-{str(user_id)}"
            user_folder.mkdir(parents=True, exist_ok=True)

            # Generate filenames
            file_extension = Path(filename).suffix.lower() or ".jpg"
            photo_filename = f"profile{file_extension}"
            thumbnail_filename = f"profile_thumb{file_extension}"

            # Full paths
            photo_path = user_folder / photo_filename
            thumbnail_path = user_folder / thumbnail_filename

            # Save image with optimization
            image = Image.open(io.BytesIO(file_content))

            # Convert RGBA to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background

            # Resize to reasonable profile photo size (max 800px)
            max_size = 800
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Save full image
            image.save(
                photo_path,
                format='JPEG',
                quality=90,
                optimize=True
            )

            # Generate and save thumbnail (150x150)
            thumbnail = image.copy()
            thumbnail.thumbnail((150, 150), Image.Resampling.LANCZOS)
            thumbnail.save(
                thumbnail_path,
                format='JPEG',
                quality=85,
                optimize=True
            )

            # Generate URL paths
            photo_url = f"{settings.STATIC_URL}/profiles/user-{str(user_id)}/{photo_filename}"
            thumbnail_url = f"{settings.STATIC_URL}/profiles/user-{str(user_id)}/{thumbnail_filename}"

            logger.info(f"Successfully uploaded profile photo for user {user_id}")

            return {
                'photo_url': photo_url,
                'thumbnail_url': thumbnail_url,
                'file_path': str(photo_path.relative_to(self.base_upload_dir))
            }

        except Exception as e:
            logger.error(f"Failed to upload profile photo: {str(e)}")
            raise Exception(f"Profile photo upload failed: {str(e)}")

    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Get file size in bytes.

        Args:
            file_path: Relative file path from upload directory

        Returns:
            File size in bytes or None if not found
        """
        try:
            full_path = self.base_upload_dir / file_path
            if full_path.exists() and full_path.is_file():
                return full_path.stat().st_size
            return None
        except Exception as e:
            logger.error(f"Failed to get file size for {file_path}: {str(e)}")
            return None


# Global instance
file_storage_service = FileStorageService()
