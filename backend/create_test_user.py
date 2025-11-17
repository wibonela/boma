"""Create test user for development."""
import asyncio
from uuid import UUID
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.enums import UserStatus


async def create_test_user():
    """Create a test user with the mock host ID."""
    async with AsyncSessionLocal() as db:
        # Check if user already exists
        test_user_id = UUID("00000000-0000-0000-0000-000000000001")
        result = await db.execute(select(User).where(User.id == test_user_id))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"Test user already exists: {existing_user.email}")
            return

        # Create new test user
        test_user = User(
            id=test_user_id,
            clerk_id="test_clerk_id_001",
            email="testhost@boma.co.tz",
            country_code="TZ",
            is_guest=False,
            is_host=True,
            is_admin=False,
            status=UserStatus.ACTIVE,
            email_verified=True,
            phone_verified=True
        )

        db.add(test_user)
        await db.commit()
        await db.refresh(test_user)

        print(f"Created test user: {test_user.email} (ID: {test_user.id})")


if __name__ == "__main__":
    asyncio.run(create_test_user())
