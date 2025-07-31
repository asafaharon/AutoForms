"""
Database transaction utilities for ensuring data consistency
"""
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession
from backend.db import get_client, get_db
from typing import AsyncContextManager
import asyncio

@asynccontextmanager
async def db_transaction() -> AsyncContextManager[AsyncIOMotorClientSession]:
    """Context manager for database transactions"""
    client = await get_client()
    
    async with await client.start_session() as session:
        try:
            async with session.start_transaction():
                yield session
                # Transaction will be committed automatically if no exception
        except Exception:
            # Transaction will be aborted automatically on exception
            raise

async def with_transaction(operation_func, *args, **kwargs):
    """Helper function to execute an operation within a transaction"""
    async with db_transaction() as session:
        return await operation_func(session, *args, **kwargs)

class TransactionManager:
    """Transaction manager for complex operations"""
    
    def __init__(self):
        self.client = None
        self.session = None
    
    async def __aenter__(self):
        self.client = await get_client()
        self.session = await self.client.start_session()
        await self.session.start_transaction()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # No exception, commit transaction
            await self.session.commit_transaction()
        else:
            # Exception occurred, abort transaction
            await self.session.abort_transaction()
        
        await self.session.end_session()
    
    async def get_database(self):
        """Get database instance with transaction session"""
        from backend.config import get_settings
        settings = get_settings()
        return self.client[settings.database_name]

# Example usage functions for common transaction patterns

async def create_form_with_transaction(form_data: dict, user_id: str):
    """Create a form with proper transaction handling"""
    async with TransactionManager() as tm:
        db = await tm.get_database()
        
        # Insert form
        result = await db.forms.insert_one(form_data, session=tm.session)
        form_id = str(result.inserted_id)
        
        # Update user's form count
        await db.users.update_one(
            {"_id": user_id},
            {"$inc": {"form_count": 1}},
            session=tm.session
        )
        
        return form_id

async def delete_form_with_transaction(form_id: str, user_id: str):
    """Delete a form and clean up related data with transaction"""
    async with TransactionManager() as tm:
        db = await tm.get_database()
        
        # Delete form
        result = await db.forms.delete_one(
            {"_id": form_id, "user_id": user_id},
            session=tm.session
        )
        
        if result.deleted_count == 0:
            raise ValueError("Form not found or access denied")
        
        # Delete all submissions for this form
        await db.form_submissions.delete_many(
            {"form_id": form_id},
            session=tm.session
        )
        
        # Update user's form count
        await db.users.update_one(
            {"_id": user_id},
            {"$inc": {"form_count": -1}},
            session=tm.session
        )
        
        return True

async def submit_form_with_transaction(form_id: str, submission_data: dict):
    """Submit form data with transaction to ensure consistency"""
    async with TransactionManager() as tm:
        db = await tm.get_database()
        
        # Check if form exists and is active
        form = await db.forms.find_one(
            {"_id": form_id, "is_active": True},
            session=tm.session
        )
        
        if not form:
            raise ValueError("Form not found or inactive")
        
        # Insert submission
        submission_result = await db.form_submissions.insert_one(
            submission_data,
            session=tm.session
        )
        
        # Update form submission count
        await db.forms.update_one(
            {"_id": form_id},
            {"$inc": {"submission_count": 1}},
            session=tm.session
        )
        
        return str(submission_result.inserted_id)