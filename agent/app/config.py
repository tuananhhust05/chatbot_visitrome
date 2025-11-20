
import logging
import os
from fastapi import FastAPI, HTTPException, Request
from dotenv import load_dotenv
from datetime import datetime

def intialize_logs():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'./log/{datetime.now().strftime("%Y%m%d%H%M%S")}.log'),        
            logging.StreamHandler()
        ]
    )

def load_env_variables(app: FastAPI):
    load_dotenv()
    app.state.ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    app.state.APP_ID = os.getenv("APP_ID")
    app.state.APP_SECRET = os.getenv("APP_SECRET")
    app.state.VERSION = os.getenv("VERSION")
    app.state.PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
    app.state.VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
    # app.state.isUAT = True if os.getenv("isUAT")=='True' else False
    app.state.isUAT = True 
    
async def get_settings(request: Request):
    if not request.app.state.ACCESS_TOKEN:
        raise Exception(status_code=500, detail="Missing ACCESS_TOKEN")
    if not request.app.state.APP_ID:
        raise HTTPException(status_code=500, detail="Missing APP_ID")
    if not request.app.state.APP_SECRET:
        raise HTTPException(status_code=500, detail="Missing APP_SECRET")
    if not request.app.state.VERSION:
        raise HTTPException(status_code=500, detail="Missing VERSION")
    if not request.app.state.VERIFY_TOKEN:
        raise HTTPException(status_code=500, detail="Missing VERIFY_TOKEN")
    if not request.app.state.PHONE_NUMBER_ID:
        raise HTTPException(status_code=500, detail="Missing PHONE_NUMBER_ID")
    if not request.app.state.isUAT:
        raise HTTPException(status_code=500, detail="Missing isUAT")
    return request.app.state





# """"""
# Yes! FastAPI offers several excellent ways to handle configuration and state management. Here are two recommended approaches:

# Using FastAPI's State:
# from fastapi import FastAPI
# from dotenv import load_dotenv
# import os

# def create_app():
#     app = FastAPI()
#     load_dotenv()
    
#     # Store config in app.state
#     app.state.ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
#     app.state.YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER")
#     app.state.APP_ID = os.getenv("APP_ID")
#     app.state.APP_SECRET = os.getenv("APP_SECRET")
#     app.state.RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")
#     app.state.VERSION = os.getenv("VERSION")
#     app.state.PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
#     app.state.VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
    
#     return app

# Copy

# Apply

# app__init__.py
# Using Pydantic Settings (recommended approach):
# from pydantic_settings import BaseSettings

# class Settings(BaseSettings):
#     ACCESS_TOKEN: str
#     YOUR_PHONE_NUMBER: str
#     APP_ID: str
#     APP_SECRET: str
#     RECIPIENT_WAID: str
#     VERSION: str
#     PHONE_NUMBER_ID: str
#     VERIFY_TOKEN: str
    
#     class Config:
#         env_file = ".env"

# # Create a global settings instance
# settings = Settings()

# Copy

# Apply

# app\config.py
# Then in your routes, you can access these settings:

# from app.config import settings

# @router.post("/")
# async def webhook(request: Request):
#     # Access settings like this
#     token = settings.ACCESS_TOKEN
#     phone_id = settings.PHONE_NUMBER_ID

# Copy

# Apply

# app\routers\whatsapp.py
# The Pydantic Settings approach offers type safety, validation, and better IDE support, making it the preferred method in FastAPI applications.



# Try again with different context
# Add context...