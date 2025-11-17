"""Quick script to create a test user for development"""
import asyncio
import sys
from sqlalchemy import select

sys.path.insert(0, '/Users/walid/Desktop/TheFILES/boma/backend')

from app.db.session import AsyncSessionLocal
from app.models.user import User

async def create_test_user():
    async with AsyncSessionLocal() as db:
        # Check if test user exists
        result = await db.execute(
            select(User).where(User.email == 'test@boma.co.tz')
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"✓ Test user already exists: {existing_user.id}")
            print(f"  Email: {existing_user.email}")
            print(f"  Roles: Guest={existing_user.is_guest}, Host={existing_user.is_host}")
            return
        
        # Create test user
        test_user = User(
            id='test-user-dev-123',
            clerk_user_id='test-clerk-dev-123',
            email='test@boma.co.tz',
            phone_number='+255754123456',
            full_name='Test User',
            is_guest=True,
            is_host=False,
            is_active=True,
            email_verified=True,
            phone_verified=True,
        )
        
        db.add(test_user)
        await db.commit()
        await db.refresh(test_user)
        
        print("✓ Test user created successfully!")
        print(f"  ID: {test_user.id}")
        print(f"  Email: {test_user.email}")
        print(f"  Phone: {test_user.phone_number}")

if __name__ == '__main__':
    asyncio.run(create_test_user())
