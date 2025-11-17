"""
Review endpoints for the BOMA API.
Handles review creation, listing, and host responses.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.booking import Booking, Review
from app.models.property import Property
from app.models.enums import BookingStatus
from app.schemas.review import (
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse,
    ReviewWithGuestInfo,
    HostResponseCreate,
    PropertyRatingSummary,
)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a review for a completed booking.

    Requirements:
    - User must be the guest of the booking
    - Booking must be completed
    - No review exists for this booking yet
    """
    # Get the booking
    result = await db.execute(
        select(Booking)
        .where(Booking.id == review_data.booking_id)
        .options(selectinload(Booking.review))
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Verify user is the guest
    if booking.guest_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only review your own bookings"
        )

    # Verify booking is completed
    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only review completed bookings"
        )

    # Check if review already exists
    if booking.review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A review already exists for this booking"
        )

    # Create the review
    review = Review(
        booking_id=booking.id,
        property_id=booking.property_id,
        host_id=booking.host_id,
        guest_id=current_user.id,
        rating=review_data.rating,
        cleanliness_rating=review_data.cleanliness_rating,
        accuracy_rating=review_data.accuracy_rating,
        communication_rating=review_data.communication_rating,
        location_rating=review_data.location_rating,
        value_rating=review_data.value_rating,
        comment=review_data.comment,
        is_public=review_data.is_public,
    )

    db.add(review)
    await db.commit()
    await db.refresh(review)

    return review


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific review by ID."""
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    return review


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: UUID,
    review_data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a review. Only the guest who created it can update.
    Host responses cannot be updated through this endpoint.
    """
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    # Verify user is the guest who created the review
    if review.guest_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own reviews"
        )

    # Update fields if provided
    update_data = review_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    await db.commit()
    await db.refresh(review)

    return review


@router.post("/{review_id}/response", response_model=ReviewResponse)
async def add_host_response(
    review_id: UUID,
    response_data: HostResponseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a host response to a review.
    Only the host of the property can respond.
    """
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    # Verify user is the host
    if review.host_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can respond to this review"
        )

    # Check if response already exists
    if review.host_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A response already exists for this review. Use PUT to update."
        )

    # Add the response
    review.host_response = response_data.host_response
    review.host_responded_at = datetime.utcnow()

    await db.commit()
    await db.refresh(review)

    return review


@router.get("/properties/{property_id}/list", response_model=List[ReviewWithGuestInfo])
async def get_property_reviews(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    public_only: bool = Query(True, description="Only show public reviews"),
):
    """
    Get all reviews for a property with pagination.
    Returns reviews with guest information.
    """
    # Verify property exists
    result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    property_obj = result.scalar_one_or_none()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Build query
    query = (
        select(Review)
        .where(Review.property_id == property_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    if public_only:
        query = query.where(Review.is_public == True)

    result = await db.execute(query)
    reviews = result.scalars().all()

    # For now, return as ReviewResponse (guest info can be added later with joins)
    return reviews


@router.get("/properties/{property_id}/rating-summary", response_model=PropertyRatingSummary)
async def get_property_rating_summary(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get rating summary for a property including:
    - Total review count
    - Average overall rating
    - Average for each category
    - Rating distribution (1-5 stars)
    """
    # Verify property exists
    result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    property_obj = result.scalar_one_or_none()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Get all public reviews for the property
    result = await db.execute(
        select(Review).where(
            and_(
                Review.property_id == property_id,
                Review.is_public == True
            )
        )
    )
    reviews = result.scalars().all()

    if not reviews:
        return PropertyRatingSummary(
            property_id=property_id,
            total_reviews=0,
            average_rating=0.0,
            rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        )

    # Calculate averages
    total_reviews = len(reviews)
    avg_rating = sum(r.rating for r in reviews) / total_reviews

    # Calculate category averages (only for reviews that have them)
    cleanliness_ratings = [r.cleanliness_rating for r in reviews if r.cleanliness_rating]
    accuracy_ratings = [r.accuracy_rating for r in reviews if r.accuracy_rating]
    communication_ratings = [r.communication_rating for r in reviews if r.communication_rating]
    location_ratings = [r.location_rating for r in reviews if r.location_rating]
    value_ratings = [r.value_rating for r in reviews if r.value_rating]

    avg_cleanliness = sum(cleanliness_ratings) / len(cleanliness_ratings) if cleanliness_ratings else None
    avg_accuracy = sum(accuracy_ratings) / len(accuracy_ratings) if accuracy_ratings else None
    avg_communication = sum(communication_ratings) / len(communication_ratings) if communication_ratings else None
    avg_location = sum(location_ratings) / len(location_ratings) if location_ratings else None
    avg_value = sum(value_ratings) / len(value_ratings) if value_ratings else None

    # Calculate rating distribution
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in reviews:
        rating_distribution[review.rating] += 1

    return PropertyRatingSummary(
        property_id=property_id,
        total_reviews=total_reviews,
        average_rating=round(avg_rating, 2),
        average_cleanliness=round(avg_cleanliness, 2) if avg_cleanliness else None,
        average_accuracy=round(avg_accuracy, 2) if avg_accuracy else None,
        average_communication=round(avg_communication, 2) if avg_communication else None,
        average_location=round(avg_location, 2) if avg_location else None,
        average_value=round(avg_value, 2) if avg_value else None,
        rating_distribution=rating_distribution
    )
