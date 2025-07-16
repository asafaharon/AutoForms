"""
Database indexes for better performance
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.db import get_db

async def create_indexes():
    """Create database indexes for better performance"""
    db = await get_db()
    
    print("📊 Creating database indexes...")
    
    try:
        # Users collection indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("username")
        await db.users.create_index("created_at")
        await db.users.create_index("is_admin")
        
        # Forms collection indexes
        await db.forms.create_index("user_id")
        await db.forms.create_index("created_at")
        await db.forms.create_index([("user_id", 1), ("created_at", -1)])  # Compound index
        
        # Submissions collection indexes
        await db.submissions.create_index("form_id")
        await db.submissions.create_index("created_at")
        await db.submissions.create_index([("form_id", 1), ("created_at", -1)])  # Compound index
        
        print("✅ Database indexes created successfully")
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        raise

async def get_collection_stats():
    """Get collection statistics for monitoring"""
    db = await get_db()
    
    stats = {}
    collections = ["users", "forms", "submissions"]
    
    for collection_name in collections:
        try:
            collection = db[collection_name]
            count = await collection.count_documents({})
            stats[collection_name] = {
                "count": count,
                "indexes": await collection.list_indexes().to_list(None)
            }
        except Exception as e:
            stats[collection_name] = {"error": str(e)}
    
    return stats