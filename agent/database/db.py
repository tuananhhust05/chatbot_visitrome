from databases import Database
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

POSTGRES_PORT = os.getenv("POSTGRES_PORT_AGENT_PRIVATE", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB_AGENT", "agent_db")
POSTGRES_USER = os.getenv("POSTGRES_USER_AGENT", "myuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD_AGENT", "mypassword")
POSTGRES_HOST = os.getenv("POSTGRES_HOST_AGENT", "localhost")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

DATABASE_CONFIG = {
    "url": DATABASE_URL,
    "max_size": 10,
    "min_size": 1,
    "max_query_duration": 5000,
    "connection_kwargs": {
        "timeout": 60,
        "ssl": None,
    },
}

database = Database(DATABASE_CONFIG["url"], min_size=DATABASE_CONFIG["min_size"], max_size=DATABASE_CONFIG["max_size"], **DATABASE_CONFIG["connection_kwargs"])

# async def webhook():
#     query = "SELECT * FROM conversations"
#     result = await database.fetch_one(query=query)
#     print("result", result)

# async def main():
#     await database.connect()
#     await webhook()
#     await database.disconnect()

# # Run the main function
# asyncio.run(main())