import logging
import uvicorn
from app import create_app
import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = create_app()

if __name__ == "__main__":
    logging.info("Fastapi app started")
    uvicorn.run(app, host="0.0.0.0", port=8501)