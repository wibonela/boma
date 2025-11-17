"""
Bookings API endpoints
Handles booking creation, payment processing, and booking management
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import uuid

from app.db.session import get_db
from app.api.v1.dependencies.auth import get_current_user
from app.models.user import User
from app.models.booking import Booking, BookingStatus
from app.models.property import Property
from app.models.payment import Payment
from app.models.enums import TransactionStatus, PaymentMethod, PaymentGateway, PaymentStatusEnum, CancellationPolicy
from app.services.azampay_service import azampay_service
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["bookings"])


# ============================================================================
# SCHEMAS
# ============================================================================

class BookingCreateRequest(BaseModel):
    """Request schema for creating a new booking"""
    property_id: str
    check_in_date: str  # ISO format: YYYY-MM-DD
    check_out_date: str  # ISO format: YYYY-MM-DD
    adults: int = Field(ge=1, le=20)
    children: int = Field(ge=0, le=20)
    infants: int = Field(ge=0, le=10)
    special_requests: Optional[str] = None

    @validator('check_in_date', 'check_out_date')
    def validate_date_format(cls, v):
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('Date must be in ISO format (YYYY-MM-DD)')


class PaymentInitiateRequest(BaseModel):
    """Request schema for initiating mobile money payment"""
    booking_id: str
    phone_number: str  # Mobile money phone number
    provider: str = Field(default="Mpesa", description="Mobile money provider")

    @validator('provider')
    def validate_provider(cls, v):
        valid_providers = azampay_service.get_supported_providers()
        if v not in valid_providers:
            raise ValueError(f'Provider must be one of: {", ".join(valid_providers)}')
        return v


class CardPaymentInitiateRequest(BaseModel):
    """Request schema for initiating card payment"""
    booking_id: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None


class BookingResponse(BaseModel):
    """Response schema for booking"""
    id: str
    property_id: str
    property_title: str
    property_photo: Optional[str]
    guest_id: str
    host_id: str
    check_in_date: str
    check_out_date: str
    nights: int
    adults: int
    children: int
    infants: int
    total_guests: int
    base_amount: float
    cleaning_fee: float
    platform_fee: float
    total_amount: float
    currency_code: str
    status: str
    payment_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Response schema for payment"""
    id: str
    booking_id: str
    amount: float
    currency_code: str
    payment_method: str
    provider: str
    status: str
    gateway_transaction_id: Optional[str]
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_booking_price(
    property_: Property,
    check_in: datetime,
    check_out: datetime
) -> dict:
    """Calculate total booking price including all fees"""
    nights = (check_out - check_in).days
    base_amount = float(property_.base_price) * nights
    cleaning_fee = float(property_.cleaning_fee) if property_.cleaning_fee else 10000.0
    subtotal = base_amount + cleaning_fee
    platform_fee = round(subtotal * 0.10, 2)  # 10% platform fee
    total = subtotal + platform_fee

    return {
        "nights": nights,
        "base_amount": base_amount,
        "cleaning_fee": cleaning_fee,
        "platform_fee": platform_fee,
        "total_amount": total
    }


async def check_availability(
    db: AsyncSession,
    property_id: str,
    check_in: datetime,
    check_out: datetime,
    exclude_booking_id: Optional[str] = None
) -> bool:
    """Check if property is available for given dates"""
    query = select(Booking).where(
        and_(
            Booking.property_id == property_id,
            Booking.status.in_([
                BookingStatus.CONFIRMED,
                BookingStatus.PENDING,
                BookingStatus.AWAITING_PAYMENT
            ]),
            or_(
                # Check for overlapping dates
                and_(
                    Booking.check_in_date <= check_in,
                    Booking.check_out_date > check_in
                ),
                and_(
                    Booking.check_in_date < check_out,
                    Booking.check_out_date >= check_out
                ),
                and_(
                    Booking.check_in_date >= check_in,
                    Booking.check_out_date <= check_out
                )
            )
        )
    )

    if exclude_booking_id:
        query = query.where(Booking.id != exclude_booking_id)

    result = await db.execute(query)
    overlapping_bookings = result.scalars().all()
    return len(overlapping_bookings) == 0


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new booking (without payment)
    Payment is initiated separately
    """
    # Get property
    result = await db.execute(select(Property).where(Property.id == booking_data.property_id))
    property_ = result.scalar_one_or_none()
    if not property_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Verify property is verified and not suspended/delisted
    from app.models.enums import PropertyStatus
    if property_.status not in [PropertyStatus.VERIFIED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property is not available for booking"
        )

    # Parse dates
    try:
        check_in = datetime.fromisoformat(booking_data.check_in_date)
        check_out = datetime.fromisoformat(booking_data.check_out_date)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )

    # Validate dates
    if check_in >= check_out:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-out date must be after check-in date"
        )

    if check_in.date() < datetime.now().date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-in date cannot be in the past"
        )

    # Check minimum nights
    nights = (check_out - check_in).days
    if nights < (property_.minimum_nights or 1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum stay is {property_.minimum_nights} night(s)"
        )

    # Check maximum guests
    total_guests = booking_data.adults + booking_data.children
    if total_guests > property_.max_guests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Property can accommodate maximum {property_.max_guests} guests"
        )

    # Check availability
    is_available = await check_availability(db, booking_data.property_id, check_in, check_out)
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Property is not available for selected dates"
        )

    # Calculate pricing
    pricing = calculate_booking_price(property_, check_in, check_out)

    # Create booking
    booking = Booking(
        property_id=property_.id,
        guest_id=current_user.id,
        host_id=property_.host_id,
        check_in_date=check_in,
        check_out_date=check_out,
        num_nights=pricing["nights"],
        num_guests=total_guests,
        base_price_per_night=float(property_.base_price),
        total_nights_cost=pricing["base_amount"],
        cleaning_fee=pricing["cleaning_fee"],
        platform_fee=pricing["platform_fee"],
        total_price=pricing["total_amount"],
        deposit_amount=0.0,  # TODO: Calculate deposit based on property settings
        currency=property_.currency,
        status=BookingStatus.AWAITING_PAYMENT,
        payment_status=PaymentStatusEnum.UNPAID,
        cancellation_policy=property_.cancellation_policy,
        special_requests=booking_data.special_requests
    )

    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    logger.info(f"Booking created: {booking.id} for user {current_user.id}")

    # Get property photo
    # TODO: Load photos with selectinload or fetch separately
    property_photo = None

    return BookingResponse(
        id=str(booking.id),
        property_id=str(booking.property_id),
        property_title=property_.title,
        property_photo=property_photo,
        guest_id=str(booking.guest_id),
        host_id=str(booking.host_id),
        check_in_date=booking.check_in_date.isoformat(),
        check_out_date=booking.check_out_date.isoformat(),
        nights=booking.num_nights,
        adults=booking_data.adults,
        children=booking_data.children,
        infants=booking_data.infants,
        total_guests=booking.num_guests,
        base_amount=booking.total_nights_cost,
        cleaning_fee=booking.cleaning_fee,
        platform_fee=booking.platform_fee,
        total_amount=booking.total_price,
        currency_code=booking.currency,
        status=booking.status.value,
        payment_status=booking.payment_status.value,
        created_at=booking.created_at
    )


@router.post("/{booking_id}/payment", response_model=PaymentResponse)
async def initiate_payment(
    booking_id: str,
    payment_data: PaymentInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate payment for a booking using AzamPay mobile money
    """
    # Get booking
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Verify user owns this booking
    if booking.guest_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to pay for this booking"
        )

    # Verify booking is in correct status
    if booking.status not in [BookingStatus.AWAITING_PAYMENT, BookingStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot initiate payment for booking with status: {booking.status}"
        )

    # Check if payment already exists
    existing_payment_result = await db.execute(
        select(Payment).where(
            and_(
                Payment.booking_id == booking_id,
                Payment.status.in_([TransactionStatus.PENDING, TransactionStatus.SUCCESS])
            )
        )
    )
    existing_payment = existing_payment_result.scalar_one_or_none()

    if existing_payment:
        if existing_payment.status == TransactionStatus.SUCCESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking already paid"
            )
        # Return existing pending payment
        return PaymentResponse(
            id=existing_payment.id,
            booking_id=existing_payment.booking_id,
            amount=existing_payment.amount,
            currency_code=existing_payment.currency,
            payment_method=existing_payment.payment_method.value,
            provider=existing_payment.phone_number,
            status=existing_payment.status.value,
            gateway_transaction_id=existing_payment.gateway_reference,
            message="Payment already initiated. Please complete the payment on your phone.",
            created_at=existing_payment.created_at
        )

    # Format phone number
    formatted_phone = azampay_service.format_phone_number(payment_data.phone_number)

    # Create payment record
    payment = Payment(
        id=str(uuid.uuid4()),
        booking_id=booking.id,
        guest_id=current_user.id,
        amount=booking.total_price,
        currency=booking.currency,
        payment_method=PaymentMethod.MOBILE_MONEY,
        phone_number=formatted_phone,
        status=TransactionStatus.PENDING,
        gateway=PaymentGateway.AZAMPAY,
        gateway_reference=str(uuid.uuid4()),  # Temporary, will be updated with actual reference
        net_amount=booking.total_price,  # Will be updated after gateway fees
        idempotency_key=str(uuid.uuid4()),
        created_at=datetime.utcnow()
    )

    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    # Initiate AzamPay checkout
    try:
        checkout_result = await azampay_service.initiate_mno_checkout(
            account_number=formatted_phone,
            amount=float(booking.total_price),
            external_id=str(booking.id),  # Use booking ID as external reference
            provider=payment_data.provider,
            currency=booking.currency
        )

        if checkout_result["success"]:
            # Update payment with transaction ID
            payment.gateway_reference = checkout_result.get("transaction_id", payment.gateway_reference)
            payment.extra_data = checkout_result
            await db.commit()

            logger.info(f"Payment initiated successfully for booking {booking_id}")

            return PaymentResponse(
                id=payment.id,
                booking_id=payment.booking_id,
                amount=payment.amount,
                currency_code=payment.currency,
                payment_method=payment.payment_method.value,
                provider=payment.phone_number,
                status=payment.status.value,
                gateway_transaction_id=payment.gateway_reference,
                message="Payment initiated. Please complete the payment on your phone.",
                created_at=payment.created_at
            )
        else:
            # Payment initiation failed
            payment.status = TransactionStatus.FAILED
            payment.extra_data = checkout_result
            await db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=checkout_result.get("message", "Payment initiation failed")
            )

    except Exception as e:
        logger.error(f"Error initiating payment: {str(e)}")
        payment.status = TransactionStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment initiation failed: {str(e)}"
        )


@router.post("/{booking_id}/payment/card", response_model=PaymentResponse)
async def initiate_card_payment(
    booking_id: str,
    payment_data: CardPaymentInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate card payment for a booking
    Returns a checkout URL that the user should be redirected to
    """
    # Get booking
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Verify user owns this booking
    if booking.guest_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to pay for this booking"
        )

    # Verify booking is in correct status
    if booking.status not in [BookingStatus.AWAITING_PAYMENT, BookingStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot initiate payment for booking with status: {booking.status}"
        )

    # Check if payment already exists
    existing_payment_result = await db.execute(
        select(Payment).where(
            and_(
                Payment.booking_id == booking_id,
                Payment.status.in_([TransactionStatus.PENDING, TransactionStatus.SUCCESS])
            )
        )
    )
    existing_payment = existing_payment_result.scalar_one_or_none()

    if existing_payment:
        if existing_payment.status == TransactionStatus.SUCCESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking already paid"
            )
        # Return existing pending payment info
        return PaymentResponse(
            id=existing_payment.id,
            booking_id=existing_payment.booking_id,
            amount=existing_payment.amount,
            currency_code=existing_payment.currency,
            payment_method=existing_payment.payment_method.value,
            provider="Card Payment",
            status=existing_payment.status.value,
            gateway_transaction_id=existing_payment.gateway_reference,
            message="Payment already initiated. Complete the payment in your browser.",
            created_at=existing_payment.created_at
        )

    # Create payment record
    payment = Payment(
        id=str(uuid.uuid4()),
        booking_id=booking.id,
        guest_id=current_user.id,
        amount=booking.total_price,
        currency=booking.currency,
        payment_method=PaymentMethod.CARD,
        phone_number=payment_data.customer_phone or "",
        status=TransactionStatus.PENDING,
        gateway=PaymentGateway.AZAMPAY,
        gateway_reference=str(uuid.uuid4()),  # Temporary, will be updated
        net_amount=booking.total_price,
        idempotency_key=str(uuid.uuid4()),
        created_at=datetime.utcnow()
    )

    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    # Initiate AzamPay card checkout
    try:
        checkout_result = await azampay_service.initiate_card_checkout(
            amount=float(booking.total_price),
            external_id=str(booking.id),
            currency=booking.currency,
            customer_email=payment_data.customer_email,
            customer_phone=payment_data.customer_phone
        )

        if checkout_result["success"]:
            # Update payment with transaction ID and checkout URL
            payment.gateway_reference = checkout_result.get("transaction_id", payment.gateway_reference)
            payment.extra_data = checkout_result
            await db.commit()

            logger.info(f"Card payment initiated for booking {booking_id}")

            return PaymentResponse(
                id=payment.id,
                booking_id=payment.booking_id,
                amount=payment.amount,
                currency_code=payment.currency,
                payment_method=payment.payment_method.value,
                provider=checkout_result.get("checkout_url", ""),  # Return checkout URL in provider field
                status=payment.status.value,
                gateway_transaction_id=payment.gateway_reference,
                message="Redirect user to checkout URL to complete payment",
                created_at=payment.created_at
            )
        else:
            # Payment initiation failed
            payment.status = TransactionStatus.FAILED
            payment.extra_data = checkout_result
            await db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=checkout_result.get("message", "Card payment initiation failed")
            )

    except Exception as e:
        logger.error(f"Error initiating card payment: {str(e)}")
        payment.status = TransactionStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Card payment initiation failed: {str(e)}"
        )


@router.post("/webhooks/azampay")
async def azampay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint for AzamPay payment callbacks
    """
    try:
        payload = await request.json()
        logger.info(f"Received AzamPay webhook: {payload}")

        # Process webhook
        result = await azampay_service.handle_webhook(payload)

        if result["success"]:
            external_id = result.get("external_id")  # This is the booking ID
            transaction_id = result.get("transaction_id")
            webhook_status = result.get("status")

            # Find booking
            booking_result = await db.execute(select(Booking).where(Booking.id == external_id))
            booking = booking_result.scalar_one_or_none()
            if not booking:
                logger.error(f"Booking not found for external_id: {external_id}")
                return {"status": "error", "message": "Booking not found"}

            # Find payment
            payment_result = await db.execute(
                select(Payment)
                .where(Payment.booking_id == booking.id)
                .order_by(Payment.created_at.desc())
            )
            payment = payment_result.scalars().first()

            if not payment:
                logger.error(f"Payment not found for booking: {booking.id}")
                return {"status": "error", "message": "Payment not found"}

            # Update payment status
            if webhook_status == "success":
                payment.status = TransactionStatus.SUCCESS
                payment.gateway_reference = transaction_id
                payment.paid_at = datetime.utcnow()

                # Update booking status
                booking.status = BookingStatus.CONFIRMED
                booking.payment_status = PaymentStatusEnum.PAID

                logger.info(f"Payment completed for booking {booking.id}")

                # TODO: Send confirmation email/SMS

            elif webhook_status == "failed":
                payment.status = TransactionStatus.FAILED
                logger.error(f"Payment failed for booking {booking.id}")

            payment.extra_data = payload
            await db.commit()

            return {"status": "success", "message": "Webhook processed"}

        else:
            logger.error(f"Webhook processing failed: {result}")
            return {"status": "error", "message": result.get("message")}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/my-bookings", response_model=List[BookingResponse])
async def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    filter_type: Optional[str] = None  # 'upcoming', 'past', 'cancelled', or None for all
):
    """
    Get all bookings for the current user with smart filtering

    Filter types:
    - upcoming: Future bookings (confirmed, awaiting_payment)
    - past: Completed bookings
    - cancelled: Cancelled bookings
    - None: All bookings
    """
    query = select(Booking).where(Booking.guest_id == current_user.id)

    now = datetime.now()

    if filter_type == "upcoming":
        # Future bookings that are confirmed or awaiting payment
        query = query.where(
            and_(
                Booking.check_in_date >= now,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.AWAITING_PAYMENT])
            )
        )
    elif filter_type == "past":
        # Past bookings (completed or checked out)
        query = query.where(
            or_(
                Booking.status == BookingStatus.COMPLETED,
                and_(
                    Booking.check_out_date < now,
                    Booking.status == BookingStatus.CONFIRMED
                )
            )
        )
    elif filter_type == "cancelled":
        # Cancelled bookings
        query = query.where(Booking.status == BookingStatus.CANCELLED)

    query = query.order_by(Booking.created_at.desc())
    result = await db.execute(query)
    bookings = result.scalars().all()

    results = []
    for booking in bookings:
        property_result = await db.execute(select(Property).where(Property.id == booking.property_id))
        property_ = property_result.scalar_one_or_none()
        property_photo = None
        if property_ and property_.photos:
            property_photo = property_.photos[0].photo_url

        results.append(BookingResponse(
            id=booking.id,
            property_id=booking.property_id,
            property_title=property_.title if property_ else "Property",
            property_photo=property_photo,
            guest_id=booking.guest_id,
            host_id=booking.host_id,
            check_in_date=booking.check_in_date.isoformat(),
            check_out_date=booking.check_out_date.isoformat(),
            nights=booking.num_nights,
            adults=0,  # Not stored in Booking model
            children=0,  # Not stored in Booking model
            infants=0,  # Not stored in Booking model
            total_guests=booking.num_guests,
            base_amount=booking.total_nights_cost,
            cleaning_fee=booking.cleaning_fee,
            platform_fee=booking.platform_fee,
            total_amount=booking.total_price,
            currency_code=booking.currency,
            status=booking.status.value,
            payment_status=booking.payment_status.value,
            created_at=booking.created_at
        ))

    return results


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific booking by ID"""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Verify user owns this booking or is the host
    if booking.guest_id != current_user.id and booking.host_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking"
        )

    property_result = await db.execute(select(Property).where(Property.id == booking.property_id))
    property_ = property_result.scalar_one_or_none()
    property_photo = None
    if property_ and property_.photos:
        property_photo = property_.photos[0].photo_url

    return BookingResponse(
        id=booking.id,
        property_id=booking.property_id,
        property_title=property_.title if property_ else "Property",
        property_photo=property_photo,
        guest_id=booking.guest_id,
        host_id=booking.host_id,
        check_in_date=booking.check_in_date.isoformat(),
        check_out_date=booking.check_out_date.isoformat(),
        nights=booking.num_nights,
        adults=0,  # Not stored in Booking model
        children=0,  # Not stored in Booking model
        infants=0,  # Not stored in Booking model
        total_guests=booking.num_guests,
        base_amount=booking.total_nights_cost,
        cleaning_fee=booking.cleaning_fee,
        platform_fee=booking.platform_fee,
        total_amount=booking.total_price,
        currency_code=booking.currency,
        status=booking.status.value,
        payment_status=booking.payment_status.value,
        created_at=booking.created_at
    )
