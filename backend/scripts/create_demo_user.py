#!/usr/bin/env python3
"""
Create demo user for testing
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import encrypt_sensitive_data


async def create_demo_user():
    """Create a demo physician user"""
    async with AsyncSessionLocal() as session:
        # Check if demo user already exists
        from sqlalchemy import select
        existing = await session.scalar(
            select(User).where(User.external_id == "demo-physician")
        )
        
        if existing:
            print("Demo user already exists")
            return
        
        # Create demo user
        demo_user = User(
            external_id="demo-physician",
            email="demo@heydok.com",
            role=UserRole.PHYSICIAN,
            encrypted_name=encrypt_sensitive_data("Dr. Demo User"),
            is_active=True,
            metadata={
                "demo": True,
                "specialization": "General Practice"
            }
        )
        
        session.add(demo_user)
        await session.commit()
        
        print("Demo user created successfully!")
        print(f"External ID: demo-physician")
        print(f"Email: demo@heydok.com")
        print(f"Role: physician")
        print(f"API Key: Use the first 32 characters of SECRET_KEY from .env")


if __name__ == "__main__":
    asyncio.run(create_demo_user()) 