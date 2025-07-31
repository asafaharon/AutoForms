#!/usr/bin/env python3
"""
Database cleanup script to remove IP addresses from existing form submissions
Run this script to clean up existing IP address data after removing IP tracking
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.db import get_db

async def cleanup_ip_addresses():
    """Remove ip_address field from all existing form submissions"""
    try:
        db = await get_db()
        
        # Count documents with IP addresses
        count_with_ip = await db.form_submissions.count_documents({"ip_address": {"$exists": True}})
        print(f"Found {count_with_ip} submissions with IP addresses")
        
        if count_with_ip == 0:
            print("No IP addresses found in database. Nothing to clean up.")
            return
        
        # Remove ip_address field from all submissions
        result = await db.form_submissions.update_many(
            {"ip_address": {"$exists": True}},
            {"$unset": {"ip_address": ""}}
        )
        
        print(f"Successfully removed IP addresses from {result.modified_count} submissions")
        
        # Verify cleanup
        remaining_count = await db.form_submissions.count_documents({"ip_address": {"$exists": True}})
        print(f"Remaining submissions with IP addresses: {remaining_count}")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧹 Starting IP address cleanup...")
    asyncio.run(cleanup_ip_addresses())
    print("✅ Cleanup completed!")