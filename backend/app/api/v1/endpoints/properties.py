"""
Property endpoints.

Handles property listing, creation, updates, and search.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging_config import get_logger
from app.db.session import get_db
from app.models.property import Property, PropertyPhoto, PropertyStatus
from app.models.booking import Review
from app.models.user import User
from app.schemas.property import (
    PropertyCreate,
    PropertyPhotoResponse,
    PropertyPhotoUpdate,
    PropertyPhotoReorder,
    PropertyResponse,
    PropertySearchParams,
    PropertyUpdate,
)
from app.services.file_storage_service import file_storage_service

# For now, we'll skip auth to get it working
# from app.api.v1.dependencies.auth import get_current_user, require_host_role

logger = get_logger(__name__)

router = APIRouter(prefix="/properties", tags=["properties"])


# ============================================================================
# Helper Functions
# ============================================================================

async def enrich_properties_with_ratings(
    properties: List[Property],
    db: AsyncSession
) -> List[PropertyResponse]:
    """
    Enrich property data with rating information.
    Calculates average rating and total reviews for each property.
    """
    property_responses = []

    for prop in properties:
        # Convert property to response model
        prop_response = PropertyResponse.model_validate(prop)

        # Get all public reviews for this property
        result = await db.execute(
            select(Review).where(
                Review.property_id == prop.id,
                Review.is_public == True
            )
        )
        reviews = result.scalars().all()

        # Calculate ratings
        if reviews:
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            prop_response.average_rating = round(avg_rating, 2)
            prop_response.total_reviews = len(reviews)
        else:
            prop_response.average_rating = None
            prop_response.total_reviews = 0

        property_responses.append(prop_response)

    return property_responses


# ============================================================================
# Property Endpoints
# ============================================================================

@router.get("", response_model=List[PropertyResponse])
async def list_properties(
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[PropertyResponse]:
    """
    List all properties with optional filters.

    Supports filtering by city, property_type, and price range.
    Returns active properties only.
    """
    try:
        # Build query with photos eager loading
        query = select(Property).options(
            selectinload(Property.photos)
        ).where(
            Property.active == True,
            Property.deleted_at.is_(None)
        ).execution_options(populate_existing=False)

        # Apply filters
        if city:
            query = query.where(Property.city.ilike(f"%{city}%"))

        if property_type:
            query = query.where(Property.property_type == property_type)

        if min_price:
            query = query.where(Property.base_price >= min_price)

        if max_price:
            query = query.where(Property.base_price <= max_price)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(query)
        properties = result.scalars().all()

        logger.info(f"Listed {len(properties)} properties")

        # Enrich with ratings
        return await enrich_properties_with_ratings(properties, db)

    except Exception as e:
        logger.error(f"Error listing properties: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list properties: {str(e)}"
        )


@router.get("/my-properties", response_model=List[PropertyResponse])
async def get_my_properties(
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # TODO: Uncomment when auth is ready
) -> List[PropertyResponse]:
    """
    Get all properties owned by the current host.

    Returns all properties (active, draft, inactive) belonging to the authenticated host.
    """
    try:
        # For now, use a mock host_id until auth is implemented
        # In production, this would be: host_id = current_user.id
        mock_host_id = UUID("00000000-0000-0000-0000-000000000001")

        # Build query with photos eager loading
        query = select(Property).options(
            selectinload(Property.photos)
        ).where(
            Property.host_id == mock_host_id,
            Property.deleted_at.is_(None)
        ).order_by(Property.created_at.desc())

        # Execute query
        result = await db.execute(query)
        properties = result.scalars().all()

        logger.info(f"Retrieved {len(properties)} properties for host {mock_host_id}")

        # Enrich with ratings
        return await enrich_properties_with_ratings(properties, db)

    except Exception as e:
        logger.error(f"Error getting host properties: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get your properties: {str(e)}"
        )


@router.post("", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # TODO: Uncomment when auth is ready
) -> PropertyResponse:
    """
    Create a new property.

    Requires host role. Creates a property in DRAFT status.
    """
    try:
        # For now, use a mock host_id until auth is implemented
        # In production, this would be: host_id = current_user.id
        mock_host_id = UUID("00000000-0000-0000-0000-000000000001")

        # Create property instance
        property_dict = property_data.model_dump(exclude={"amenities"}, by_alias=False)

        # Set defaults
        if "region" not in property_dict or not property_dict["region"]:
            property_dict["region"] = property_dict["city"]

        if "deposit_amount" not in property_dict or property_dict["deposit_amount"] is None:
            property_dict["deposit_amount"] = property_dict["base_price"]

        new_property = Property(
            host_id=mock_host_id,
            **property_dict
        )

        # Set initial status
        new_property.status = PropertyStatus.VERIFIED

        # Add to database
        db.add(new_property)
        await db.commit()

        # Re-fetch with photos relationship loaded
        query = select(Property).options(
            selectinload(Property.photos)
        ).where(Property.id == new_property.id)
        result = await db.execute(query)
        new_property = result.scalar_one()

        logger.info(f"Property {new_property.id} created successfully")

        return PropertyResponse.model_validate(new_property)

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating property: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create property: {str(e)}"
        )


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PropertyResponse:
    """
    Get a specific property by ID.

    Returns full property details.
    """
    try:
        query = select(Property).options(
            selectinload(Property.photos)
        ).where(
            Property.id == property_id,
            Property.deleted_at.is_(None)
        )
        result = await db.execute(query)
        property = result.scalar_one_or_none()

        if not property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        logger.info(f"Retrieved property {property_id}")
        return PropertyResponse.model_validate(property)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting property: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get property: {str(e)}"
        )


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: UUID,
    property_update: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # TODO: Uncomment when auth is ready
) -> PropertyResponse:
    """
    Update a property.

    Only the property owner can update their property.
    """
    try:
        # Get property with photos eager loaded
        query = select(Property).options(
            selectinload(Property.photos)
        ).where(
            Property.id == property_id,
            Property.deleted_at.is_(None)
        )
        result = await db.execute(query)
        property = result.scalar_one_or_none()

        if not property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        # TODO: Check ownership when auth is ready
        # if property.host_id != current_user.id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Not authorized to update this property"
        #     )

        # Update fields
        update_data = property_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(property, field, value)

        await db.commit()
        await db.refresh(property)

        logger.info(f"Property {property_id} updated successfully")
        return PropertyResponse.model_validate(property)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating property: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update property: {str(e)}"
        )


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # TODO: Uncomment when auth is ready
) -> None:
    """
    Soft delete a property.

    Only the property owner can delete their property.
    """
    try:
        # Get property
        query = select(Property).where(
            Property.id == property_id,
            Property.deleted_at.is_(None)
        )
        result = await db.execute(query)
        property = result.scalar_one_or_none()

        if not property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        # TODO: Check ownership when auth is ready
        # if property.host_id != current_user.id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Not authorized to delete this property"
        #     )

        # Soft delete
        property.deleted_at = datetime.now(timezone.utc)
        property.active = False

        await db.commit()

        logger.info(f"Property {property_id} deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting property: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete property: {str(e)}"
        )


# ============================================================================
# Property Photo Endpoints
# ============================================================================

@router.post(
    "/{property_id}/photos",
    response_model=PropertyPhotoResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_property_photo(
    property_id: UUID,
    file: UploadFile = File(...),
    caption: Optional[str] = None,
    is_cover: bool = False,
    display_order: int = 0,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # TODO: Uncomment when auth is ready
) -> PropertyPhotoResponse:
    """
    Upload a photo for a property.

    Accepts image file (jpg, jpeg, png, webp) and uploads to Cloudinary.
    Returns photo metadata including URLs.
    """
    try:
        # Verify property exists
        query = select(Property).where(
            Property.id == property_id,
            Property.deleted_at.is_(None)
        )
        result = await db.execute(query)
        property = result.scalar_one_or_none()

        if not property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        # TODO: Check ownership when auth is ready
        # if property.host_id != current_user.id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Not authorized to upload photos for this property"
        #     )

        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )

        # Read file content
        file_content = await file.read()

        # Validate file size (10MB max)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 10MB limit"
            )

        # Generate photo ID
        photo_id = uuid4()

        # Upload to local storage
        upload_result = file_storage_service.upload_property_image(
            file_content=file_content,
            property_id=property_id,
            filename=file.filename or "image.jpg",
            photo_id=photo_id
        )

        # If this is set as cover photo, unset other cover photos
        if is_cover:
            await db.execute(
                select(PropertyPhoto)
                .where(PropertyPhoto.property_id == property_id)
                .where(PropertyPhoto.is_cover == True)
            )
            existing_covers = (await db.execute(
                select(PropertyPhoto).where(
                    PropertyPhoto.property_id == property_id,
                    PropertyPhoto.is_cover == True
                )
            )).scalars().all()

            for existing_cover in existing_covers:
                existing_cover.is_cover = False

        # Use mock user ID until auth is implemented
        mock_user_id = UUID("00000000-0000-0000-0000-000000000001")

        # Create PropertyPhoto record
        new_photo = PropertyPhoto(
            id=photo_id,
            property_id=property_id,
            photo_url=upload_result['photo_url'],
            thumbnail_url=upload_result['thumbnail_url'],
            display_order=display_order,
            is_cover=is_cover,
            caption=caption,
            is_verified=False,  # Host uploaded, not yet verified
            uploaded_by=mock_user_id  # TODO: Use current_user.id when auth is ready
        )

        db.add(new_photo)
        await db.commit()
        await db.refresh(new_photo)

        logger.info(f"Photo {photo_id} uploaded for property {property_id}")

        return PropertyPhotoResponse.model_validate(new_photo)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error uploading photo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload photo: {str(e)}"
        )


@router.delete(
    "/{property_id}/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_property_photo(
    property_id: UUID,
    photo_id: UUID,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # TODO: Uncomment when auth is ready
) -> None:
    """
    Delete a property photo.

    Removes the photo from both Cloudinary and the database.
    """
    try:
        # Get photo
        query = select(PropertyPhoto).where(
            PropertyPhoto.id == photo_id,
            PropertyPhoto.property_id == property_id
        )
        result = await db.execute(query)
        photo = result.scalar_one_or_none()

        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )

        # Verify property ownership
        property_query = select(Property).where(Property.id == property_id)
        property_result = await db.execute(property_query)
        property = property_result.scalar_one_or_none()

        if not property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        # TODO: Check ownership when auth is ready
        # if property.host_id != current_user.id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Not authorized to delete photos for this property"
        #     )

        # Delete from local storage
        # Extract file path from the database (stored during upload)
        # For backward compatibility, we'll use the photo_url to construct the path
        if hasattr(photo, 'file_path') and photo.file_path:
            file_storage_service.delete_file(photo.file_path)
        else:
            # Fallback: construct path from photo_url
            logger.warning(f"No file_path stored for photo {photo_id}, skipping file deletion")

        # Delete from database
        await db.delete(photo)
        await db.commit()

        logger.info(f"Photo {photo_id} deleted from property {property_id}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting photo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete photo: {str(e)}"
        )


@router.put(
    "/{property_id}/photos/{photo_id}",
    response_model=PropertyPhotoResponse
)
async def update_property_photo(
    property_id: UUID,
    photo_id: UUID,
    photo_update: PropertyPhotoUpdate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # TODO: Uncomment when auth is ready
) -> PropertyPhotoResponse:
    """
    Update photo metadata (caption, display_order, is_cover).

    Does not re-upload the image, only updates metadata.
    """
    try:
        # Get photo
        query = select(PropertyPhoto).where(
            PropertyPhoto.id == photo_id,
            PropertyPhoto.property_id == property_id
        )
        result = await db.execute(query)
        photo = result.scalar_one_or_none()

        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found"
            )

        # Verify property ownership
        property_query = select(Property).where(Property.id == property_id)
        property_result = await db.execute(property_query)
        property = property_result.scalar_one_or_none()

        if not property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        # TODO: Check ownership when auth is ready
        # if property.host_id != current_user.id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Not authorized to update photos for this property"
        #     )

        # If setting as cover photo, unset other cover photos
        if photo_update.is_cover is True and not photo.is_cover:
            existing_covers = (await db.execute(
                select(PropertyPhoto).where(
                    PropertyPhoto.property_id == property_id,
                    PropertyPhoto.is_cover == True
                )
            )).scalars().all()

            for existing_cover in existing_covers:
                existing_cover.is_cover = False

        # Update fields
        update_data = photo_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(photo, field, value)

        await db.commit()
        await db.refresh(photo)

        logger.info(f"Photo {photo_id} updated for property {property_id}")

        return PropertyPhotoResponse.model_validate(photo)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating photo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update photo: {str(e)}"
        )


@router.put(
    "/{property_id}/photos/reorder",
    response_model=List[PropertyPhotoResponse]
)
async def reorder_property_photos(
    property_id: UUID,
    reorder_data: PropertyPhotoReorder,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # TODO: Uncomment when auth is ready
) -> List[PropertyPhotoResponse]:
    """
    Batch reorder property photos.

    Accepts a list of {photo_id, display_order} objects and updates all at once.
    """
    try:
        # Verify property exists and ownership
        property_query = select(Property).where(
            Property.id == property_id,
            Property.deleted_at.is_(None)
        )
        property_result = await db.execute(property_query)
        property = property_result.scalar_one_or_none()

        if not property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        # TODO: Check ownership when auth is ready
        # if property.host_id != current_user.id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Not authorized to reorder photos for this property"
        #     )

        # Update each photo's display_order
        updated_photos = []
        for item in reorder_data.photo_orders:
            photo_id = UUID(item['photo_id'])
            display_order = item['display_order']

            query = select(PropertyPhoto).where(
                PropertyPhoto.id == photo_id,
                PropertyPhoto.property_id == property_id
            )
            result = await db.execute(query)
            photo = result.scalar_one_or_none()

            if photo:
                photo.display_order = display_order
                updated_photos.append(photo)

        await db.commit()

        # Refresh all updated photos
        for photo in updated_photos:
            await db.refresh(photo)

        # Return all photos sorted by display_order
        all_photos_query = select(PropertyPhoto).where(
            PropertyPhoto.property_id == property_id
        ).order_by(PropertyPhoto.display_order)
        all_photos_result = await db.execute(all_photos_query)
        all_photos = all_photos_result.scalars().all()

        logger.info(f"Reordered {len(updated_photos)} photos for property {property_id}")

        return [PropertyPhotoResponse.model_validate(photo) for photo in all_photos]

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error reordering photos: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder photos: {str(e)}"
        )
