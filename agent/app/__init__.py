from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import load_env_variables, intialize_logs
from .routers import whatsapp, pdf_upload, database_management, rules
from database.db import database

API_PREFIX = "/api"

def create_app():
    app = FastAPI(title="WhatApp API", version="0.0.1")
    
    # Cấu hình CORS để cho phép tất cả origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Cho phép tất cả origins
        allow_credentials=True,
        allow_methods=["*"],  # Cho phép tất cả HTTP methods
        allow_headers=["*"],  # Cho phép tất cả headers
    )
    
    @app.on_event("startup")
    async def startup():
        try:
            await database.connect()
            print("Connected database")
        except Exception as e:
            print(f"An unexpected error when connect to database: {e}")
    @app.on_event("shutdown")
    async def shutdown():
        try:
            await database.disconnect()
            print("Connected database")
        except Exception as e:
            print(f"An unexpected error when connect to database: {e}")
        
    # Load configurations and logging settings
    load_env_variables(app)
    # intialize_logs()

    # Import and register blueprints, if any (called blueprints in Flask)
    app.include_router(whatsapp.router, prefix=API_PREFIX)
    app.include_router(pdf_upload.router, prefix=API_PREFIX)
    app.include_router(database_management.router, prefix=API_PREFIX)
    app.include_router(rules.router, prefix=API_PREFIX)

    return app
