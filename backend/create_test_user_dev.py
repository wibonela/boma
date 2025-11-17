"""Create development test user"""
import asyncio
import sys
import uuid
sys.path.insert(0, '/Users/walid/Desktop/TheFILES/boma/backend')

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User

async def create_dev_user():
    async with AsyncSessionLocal() as db:
        # Check if exists
        result = await db.execute(
            select(User).where(User.clerk_id == 'test-clerk-dev-123')
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"✓ Test user exists: {existing.id}")
            print(f"  Email: {existing.email}")
            return existing.id
        
        # Create new with proper UUID
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            clerk_id='test-clerk-dev-123',
            email='testdev@boma.co.tz',
            phone_number='+255754123456',
            country_code='TZ',
            is_guest=True,
            is_host=False,
            is_admin=False,
            status='active',
            email_verified=True,
            phone_verified=True,
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print(f"✓ Created test user: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Clerk ID: {user.clerk_id}")
        return user.id

if __name__ == '__main__':
    asyncio.run(create_dev_user())
