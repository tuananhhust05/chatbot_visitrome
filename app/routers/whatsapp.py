from fastapi import APIRouter, Depends, Request, Query, responses, FastAPI, HTTPException
from fastapi.templating import Jinja2Templates
from database.db import database
from typing import Optional
import requests
import base64

# from starlette.datastructures import State

import os, json
import logging

from app.config import get_settings
from app.utils.whatsapp.status import is_valid_whatsapp_status
from app.utils.whatsapp.message_inbound import is_valid_whatsapp_message, process_whatsapp_message
from app.utils.whatsapp.message_outbound import send_whatsapp_text
from app.controllers.whatsapp import handle_get_event_types, handle_get_user_availability_schedules,handle_get_events, handle_get_accesstoken, handle_webhook, handle_verify, handle_get_messages, handle_get_conversations 
from app.decorators.security import signature_required

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, TypedDict, cast

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool


from agents.chat.property_agent import graph
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
DB_URI = DATABASE_URL
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}


logger = logging.getLogger(__name__)
key = os.getenv('KEY')

# Strict typing approach
class State(TypedDict):
    agent: graph


@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncIterator[State]:
    async with AsyncConnectionPool(
        # conninfo=DB_URI,
        # max_size=4,
        # kwargs=connection_kwargs
        conninfo=DB_URI,
        min_size=1, 
        max_size=2,                         # Giảm từ 4 xuống 2
        max_lifetime=120,                   # Connection sống tối đa 2 phút
        max_idle=60,                        # Idle tối đa 1 phút
        kwargs=connection_kwargs
    ) as pool:
         
         # code to execute when app is loading
        checkpointer = AsyncPostgresSaver(pool)
        # await checkpointer.setup() # NOTE: you need to call .setup() the first time you're using your checkpointer (to initialize the tables in DB)

        agent=graph()
        await agent.intialize_graph(checkpointer=checkpointer)
        print("agent",agent)
        yield {"agent": agent, "db_pool": pool}
        # await pool.close()

templates = Jinja2Templates(directory="app/views")

router = APIRouter(
    prefix="/webhook",
    tags=["whatsapp"],
    lifespan=lifespan,
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)


# --------------------------------------------------------------
# Endpoint verification
# --------------------------------------------------------------
@router.get("") 
async def verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    settings = Depends(get_settings)
):
   return await handle_verify(hub_mode,hub_challenge,hub_verify_token,settings)

# --------------------------------------------------------------
# INBOUND MESSAGE HANDLER
# --------------------------------------------------------------
@router.post("")
# @signature_required
async def webhook(request: Request):
    return await handle_webhook(request)

@router.get("/conversations")
async def get_conversations(settings=Depends(get_settings)):
    return await handle_get_conversations()
    
@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: int, settings=Depends(get_settings)):
    return await handle_get_messages(conversation_id)

@router.get("/view")
async def render_conversations_html(request: Request, settings=Depends(get_settings)):
    return templates.TemplateResponse("conversations.html",{"request": request})

@router.get("/auth")
async def render_auth_html(request: Request, settings=Depends(get_settings)):
    data = await handle_get_event_types("1")
    return templates.TemplateResponse("auth.html",{"request": request, "event_data":data["event_types"]["collection"]})

@router.get("/calendly/auth/getaccesstoken/{phone_agent}/{authorization_code}")
async def getaccesstoken(phone_agent:str,authorization_code:str, settings=Depends(get_settings)):
    return await handle_get_accesstoken(phone_agent,authorization_code)

@router.get("/calendly/events/{phone_agent}")
async def getevents(phone_agent: str, min_start_time:Optional[str] = None,
                    max_start_time: Optional[str] = None, 
                    settings=Depends(get_settings)):
    return await handle_get_events(phone_agent,min_start_time,max_start_time)

@router.get("/calendly/user_availability_schedules/{phone_agent}")
# @signature_required
async def user_availability_schedules(phone_agent: str, settings=Depends(get_settings)):
    return await handle_get_user_availability_schedules(phone_agent)

@router.get("/calendly/event_types/{phone_agent}")
# @signature_required
async def event_types(phone_agent: str, settings=Depends(get_settings)):
    return await handle_get_event_types(phone_agent)