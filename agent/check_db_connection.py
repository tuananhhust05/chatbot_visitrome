#!/usr/bin/env python3
"""
Test database connection script
"""

import os
import asyncio
from databases import Database
from dotenv import load_dotenv
load_dotenv()

async def test_database_connection():
    """Test database connection"""
    POSTGRES_PORT = os.getenv("POSTGRES_PORT_AGENT_PRIVATE", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB_AGENT", "agent_db")
    POSTGRES_USER = os.getenv("POSTGRES_USER_AGENT", "myuser")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD_AGENT", "mypassword")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST_AGENT", "localhost")

    # Tạo connection string
    DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    # Get database URL from environment
    database_url = DATABASE_URL
    
    print(f"Testing database connection to: {database_url}")
    
    # Create database instance
    database = Database(database_url)
    
    try:
        # Connect to database
        await database.connect()
        print("✅ Successfully connected to database!")
        
        # Test a simple query
        result = await database.fetch_one("SELECT 1 as test")
        print(f"✅ Query test successful: {result}")
        
        # Check if tables exist
        tables_result = await database.fetch_all("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        print("📋 Available tables:")
        for table in tables_result:
            print(f"  - {table['table_name']}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        await database.disconnect()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_database_connection())
    exit(0 if success else 1)

