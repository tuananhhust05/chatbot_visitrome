import json
import os 
import logging
import traceback
import sys
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import  Depends, Request, Query, responses, HTTPException
from database.db import database
from app.utils.whatsapp.message_inbound import is_valid_whatsapp_message, process_whatsapp_message
from app.utils.whatsapp.status import is_valid_whatsapp_status
from app.config import get_settings
from app.utils.whatsapp.message_outbound import send_whatsapp_text
from dotenv import load_dotenv
import requests
import base64
import time 
import asyncio

import weaviate
from sentence_transformers import SentenceTransformer

load_dotenv()
key = os.getenv('KEY')

# Your username an
# d password for calendly login 
username = os.getenv('client_id')
password = os.getenv('client_secret')
# Combine username and password in the format 'username:password'
credentials = f"{username}:{password}"
# Base64 encode the credentials
encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
_travel_embedding_model = SentenceTransformer('all-distilroberta-v1')
_weaviate_client = weaviate.Client(WEAVIATE_URL)
_TRAVEL_VECTOR_FIELDS = ["category", "content", "url", "doc_id", "chunk_id", "agentId"]
_TRAVEL_CLASS_HOTELS = "Hotels"
_TRAVEL_CLASS_TOURS = "Tours"


def _parse_travel_content(raw_content: str):
    try:
        parsed = json.loads(raw_content)
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {}


def _format_hotel_record(record: dict) -> dict:
    payload = _parse_travel_content(record.get("content", ""))
    metadata = {
        "score": record.get("_additional", {}).get("score"),
        "distance": record.get("_additional", {}).get("distance"),
    }
    return {
        "id": payload.get("id") or payload.get("hotel_id") or record.get("doc_id"),
        "name": payload.get("name"),
        "city": payload.get("city"),
        "country": payload.get("country"),
        "price_range": payload.get("price_range") or payload.get("price"),
        "description": payload.get("des") or payload.get("description"),
        "link": payload.get("link") or record.get("url"),
        "metadata": metadata,
    }


def _format_tour_record(record: dict) -> dict:
    payload = _parse_travel_content(record.get("content", ""))
    provider = payload.get("provider") or {}
    items = payload.get("items", [])
    metadata = {
        "score": record.get("_additional", {}).get("score"),
        "distance": record.get("_additional", {}).get("distance"),
    }
    return {
        "id": payload.get("tour_id") or payload.get("id") or record.get("doc_id"),
        "name": payload.get("tour_name") or payload.get("name"),
        "city": payload.get("city"),
        "country": payload.get("country"),
        "provider": provider.get("name"),
        "link": provider.get("website") or record.get("url"),
        "highlights": [item.get("location_name") or item.get("description") for item in items if isinstance(item, dict)],
        "metadata": metadata,
    }


def _query_travel_class(class_name: str, vector: list, agent_id: str, limit: int):
    normalized_class = _TRAVEL_CLASS_HOTELS if class_name.lower().startswith("hotel") else (
        _TRAVEL_CLASS_TOURS if class_name.lower().startswith("tour") else class_name
    )
    response = (
        _weaviate_client.query
        .get(normalized_class, _TRAVEL_VECTOR_FIELDS)
        .with_where({
            "path": ["agentId"],
            "operator": "Equal",
            "valueString": agent_id
        })
        .with_limit(limit)
        .with_additional(["score", "distance"])
        .with_near_vector({"vector": vector})
        .do()
    )
    return response.get("data", {}).get("Get", {}).get(normalized_class, []) or []


def _fetch_relevant_travel_data_sync(text: str, agent_id: str = "1", limit: int = 3) -> dict:
    if not text:
        return {"hotels": [], "tours": []}

    try:
        vector = _travel_embedding_model.encode(text).tolist()
    except Exception as exc:
        logging.warning("Failed to encode travel text: %s", exc)
        return {"hotels": [], "tours": []}

    relevant = {"hotels": [], "tours": []}
    try:
        hotel_hits = _query_travel_class("hotels", vector, agent_id, limit)
        relevant["hotels"] = [_format_hotel_record(hit) for hit in hotel_hits]
    except Exception as exc:
        logging.warning("Hotel relevance lookup failed: %s", exc)

    try:
        tour_hits = _query_travel_class("tours", vector, agent_id, limit)
        relevant["tours"] = [_format_tour_record(hit) for hit in tour_hits]
    except Exception as exc:
        logging.warning("Tour relevance lookup failed: %s", exc)

    return relevant


async def get_relevant_travel_data(text: str, agent_id: str = "1", limit: int = 3) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _fetch_relevant_travel_data_sync(text, agent_id, limit))


# --------------------------------------------------------------
# INBOUND MESSAGE HANDLER
# --------------------------------------------------------------

async def handle_webhook(request:Request):
    error_details = {
        "timestamp": datetime.now().isoformat(),
        "request_info": {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else "unknown"
        }
    }
    
    try:
        # Get the JSON payload from the request
        payload = await request.json()
        logging.info(f"Payload: {payload}")
        error_details["payload"] = payload

        # Check if it's a simple JSON message (not WhatsApp webhook format)
        if "message" in payload or "text" in payload:
            logging.info("Received a simple JSON message.")
            
            try:
                agent = request.state.agent
                error_details["agent_available"] = agent is not None
            except Exception as e:
                error_details["agent_error"] = {
                    "type": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc()
                }
                return JSONResponse(
                    content={
                        "status": "error", 
                        "message": "Agent initialization failed",
                        "error_details": error_details
                    },
                    status_code=500
                )
            
            # Extract message from simple JSON format
            input_message = payload.get("message", payload.get("text", ""))
            if not input_message:
                error_details["validation_error"] = "No message found in payload"
                return JSONResponse(
                    content={
                        "status": "error", 
                        "message": "No message found in payload",
                        "error_details": error_details
                    },
                    status_code=400
                )
            
            try:
                agentId = "1"
                client_id = payload["client_id"]
                error_details["extracted_data"] = {
                    "agentId": agentId,
                    "client_id": client_id,
                    "input_message": input_message
                }
                
                print("start query")
                query_find = f"SELECT * FROM conversations WHERE members @> ARRAY['{agentId}', '{client_id}'] AND array_length(members, 1) = 2"
                error_details["database_queries"] = {"find_query": query_find}
                
                results = await database.fetch_all(query=query_find)
                print("finish first query", results)
                error_details["database_queries"]["find_results"] = str(results)
                
                if len(results) < 1:
                    query = f"INSERT INTO conversations (members, created_at, updated_at, agentid) VALUES (ARRAY['{agentId}', '{client_id}'], EXTRACT(EPOCH FROM CURRENT_TIMESTAMP), EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),{agentId})"
                    error_details["database_queries"]["insert_query"] = query
                    
                    await database.fetch_one(query)
                    print("inserted con")
                    
                    results = await database.fetch_all(query=query_find)
                    error_details["database_queries"]["insert_results"] = str(results)
                    
                    if len(results) > 0:
                        conversation_id = dict(results[0])["id"]
                        error_details["conversation_id"] = conversation_id
                    else:
                        error_details["database_error"] = "Failed to retrieve conversation after insert"
                        logging.error("Error inserting conversation.")
                        return JSONResponse(
                            content={
                                "status": "error", 
                                "message": "Error inserting conversation.",
                                "error_details": error_details
                            }, 
                            status_code=400
                        )
                else:
                    conversation_id = dict(results[0])["id"]
                    error_details["conversation_id"] = conversation_id
                
                input_message_with_key = f"{input_message}{key}{conversation_id}"
                print(f"Input message: {input_message_with_key}")
                error_details["processed_message"] = input_message_with_key
                query = """
                    INSERT INTO messages (conversation_id, sender, content, type, from_ai, created_at, updated_at, is_summarized)
                    VALUES (:conversation_id, :sender, :content, 'text', 0, EXTRACT(EPOCH FROM NOW()), EXTRACT(EPOCH FROM NOW()), 0)
                """
                params = {
                    "conversation_id": conversation_id,
                    "sender": client_id,
                    "content": payload['message'],
                }
                await database.fetch_one(query, values=params)
                # Call to agent
                reply = await agent.chat(input=input_message_with_key, config={"configurable": {"thread_id": "10"}})
                print("reply", reply)
                query = """
                    INSERT INTO messages (conversation_id, sender, content, type, from_ai, created_at, updated_at, is_summarized)
                    VALUES (:conversation_id, :sender, :content, 'text', 1, EXTRACT(EPOCH FROM NOW()), EXTRACT(EPOCH FROM NOW()), 0)
                """
                params = {
                    "conversation_id": conversation_id,
                    "sender": agentId,
                    "content": reply,
                }
                await database.fetch_one(query, values=params)
                error_details["agent_reply"] = str(reply)

                relevant_data = await get_relevant_travel_data(input_message, agentId)
                error_details["relevant_data_preview"] = {
                    "hotels": len(relevant_data.get("hotels", [])),
                    "tours": len(relevant_data.get("tours", []))
                }
                
                return JSONResponse(
                    content={"status": "ok", "reply": reply, "relevant_data": relevant_data},
                    status_code=200
                )
                
            except KeyError as e:
                error_details["key_error"] = {
                    "type": "KeyError",
                    "message": f"Missing required key: {str(e)}",
                    "available_keys": list(payload.keys()) if isinstance(payload, dict) else "Not a dict",
                    "traceback": traceback.format_exc()
                }
                return JSONResponse(
                    content={
                        "status": "error", 
                        "message": f"Missing required field: {str(e)}",
                        "error_details": error_details
                    },
                    status_code=400
                )
            except Exception as e:
                error_details["processing_error"] = {
                    "type": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc()
                }
                return JSONResponse(
                    content={
                        "status": "error", 
                        "message": f"Error processing message: {str(e)}",
                        "error_details": error_details
                    },
                    status_code=500
                )
        
        else:
            error_details["validation_error"] = "Invalid payload format - missing 'message' or 'text' field"
            error_details["payload_keys"] = list(payload.keys()) if isinstance(payload, dict) else "Not a dict"
            return JSONResponse(
                content={
                    "status": "error", 
                    "message": "Invalid payload format",
                    "error_details": error_details
                },
                status_code=400
            )

    except json.JSONDecodeError as e:
        error_details["json_error"] = {
            "type": "JSONDecodeError",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        traceback.print_exc()
        logging.error("Failed to decode JSON")
        return JSONResponse(
            content={
                "status": "error", 
                "message": "Invalid JSON provided",
                "error_details": error_details
            },
            status_code=400
        )
    except Exception as e:
        error_details["unexpected_error"] = {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        traceback.print_exc()
        logging.error(f"Unexpected error in webhook: {str(e)}")
        return JSONResponse(
            content={
                "status": "error", 
                "message": f"Internal server error: {str(e)}",
                "error_details": error_details
            },
            status_code=500
        )

# --------------------------------------------------------------
# Endpoint verification
# --------------------------------------------------------------
async def handle_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    settings = Depends(get_settings)
):
    error_details = {
        "timestamp": datetime.now().isoformat(),
        "verification_info": {
            "hub_mode": hub_mode,
            "hub_challenge": hub_challenge,
            "hub_verify_token": hub_verify_token,
            "expected_verify_token": settings.VERIFY_TOKEN if hasattr(settings, 'VERIFY_TOKEN') else "NOT_SET"
        }
    }
    
    try:
        verify_token = settings.VERIFY_TOKEN
        logging.info("GET request received")
        
        # Check if a token and mode were sent
        if hub_mode and hub_verify_token:
            # Check the mode and token sent are correct
            if hub_mode == "subscribe" and hub_verify_token == verify_token:
                # Respond with 200 OK and challenge token from the request
                logging.info("WEBHOOK_VERIFIED")
                cleaned_challenge = hub_challenge.strip("\"").strip("\\").strip()
                error_details["verification_status"] = "SUCCESS"
                return responses.JSONResponse(content=cleaned_challenge, status_code=200)
            else:
                # Responds with '403 Forbidden' if verify tokens do not match
                error_details["verification_status"] = "FAILED"
                error_details["failure_reason"] = {
                    "mode_match": hub_mode == "subscribe",
                    "token_match": hub_verify_token == verify_token,
                    "expected_mode": "subscribe",
                    "received_mode": hub_mode
                }
                logging.info("VERIFICATION_FAILED")
                return responses.JSONResponse(
                    content={
                        "status": "error", 
                        "message": "Verification failed",
                        "error_details": error_details
                    }, 
                    status_code=403
                )
        else:
            # Responds with '400 Bad Request' parameters are missing
            error_details["verification_status"] = "MISSING_PARAMETERS"
            error_details["missing_parameters"] = {
                "hub_mode": hub_mode is None,
                "hub_verify_token": hub_verify_token is None
            }
            logging.info("MISSING_PARAMETER")
            return responses.JSONResponse(
                content={
                    "status": "error", 
                    "message": "Missing parameters",
                    "error_details": error_details
                }, 
                status_code=400
            )
    except Exception as e:
        error_details["verification_error"] = {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        logging.error(f"Error in verification: {str(e)}")
        return responses.JSONResponse(
            content={
                "status": "error", 
                "message": f"Verification error: {str(e)}",
                "error_details": error_details
            }, 
            status_code=500
        )

async def handle_get_messages(conversation_id: int, settings=Depends(get_settings)):
    error_details = {
        "timestamp": datetime.now().isoformat(),
        "conversation_id": conversation_id
    }
    
    try:
        query = "SELECT * FROM messages WHERE conversation_id = :conversation_id ORDER BY id DESC"
        error_details["database_query"] = query
        
        results = await database.fetch_all(query=query, values={"conversation_id": conversation_id})
        error_details["query_results_count"] = len(results) if results else 0
        
        if results:
            return {"status": "ok", "messages": results}
        else:
            error_details["error_type"] = "NO_MESSAGES_FOUND"
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": "No messages found for this conversation",
                    "error_details": error_details
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        error_details["database_error"] = {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Database error: {str(e)}",
                "error_details": error_details
            }
        )

async def handle_get_conversations(settings=Depends(get_settings)):
    error_details = {
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        query = "SELECT * FROM conversations"
        error_details["database_query"] = query
        
        results = await database.fetch_all(query=query)
        error_details["query_results_count"] = len(results) if results else 0
        
        if results:
            return {"status": "ok", "conversations": results}
        else:
            error_details["error_type"] = "NO_CONVERSATIONS_FOUND"
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": "No conversations found",
                    "error_details": error_details
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        error_details["database_error"] = {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Database error: {str(e)}",
                "error_details": error_details
            }
        )

async def handle_get_accesstoken(phone_agent: str,authorization_code:str, settings=Depends(get_settings)):
    # Define the URL and data for the POST request
    url = 'https://auth.calendly.com/oauth/token'
    data = {
        'grant_type': 'authorization_code',
        'code': authorization_code,  # Using dynamic authorization_code
        'redirect_uri': 'https://traco.asia/webhook/auth',
        'code_verifier': 'jjjdekdekd'
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}'
    }

    try:
        query = f"SELECT * FROM manage_token WHERE phone='{phone_agent}'"
        results = await database.fetch_all(query=query)
        if(len(results) > 0 ):
            token_data = eval(results[0]['token'])
            expired_time = token_data['created_at'] + token_data['expires_in']
            if(expired_time > int(time.time())):
                print("not expired ....")
                return {"status": "ok", "token": token_data}
            
            print("resfresh token")
            data_refresh = {
                'grant_type': 'refresh_token',
                'refresh_token': token_data['refresh_token'] 
            }
            response = requests.post(url, data=data_refresh, headers=headers)
            # Check if the response is successful
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Error from Calendly API: {response.text}")

            # Perform database operations
            query_delete = "DELETE FROM manage_token WHERE phone = :phone"
            await database.fetch_all(query=query_delete, values={"phone": phone_agent})

            query_insert = """
            INSERT INTO manage_token (phone, token)
            VALUES (:phone, :token)
            """
            
            # Ensure token is a valid JSON format (serializing to JSON)
            token_json = json.dumps(response.json())  # Use .json() for structured response
            
            # Execute the insert query
            await database.execute(query=query_insert, values={"phone": phone_agent, "token": token_json})
            print("token_json refresh...", token_json)
            # Return success response
            return {"status": "ok", "token": eval(token_json)}
        else:
            # Sending the POST request
            response = requests.post(url, data=data, headers=headers)

            # Check if the response is successful
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Error from Calendly API: {response.text}")

            # Perform database operations
            query_delete = "DELETE FROM manage_token WHERE phone = :phone"
            await database.fetch_all(query=query_delete, values={"phone": phone_agent})

            query_insert = """
            INSERT INTO manage_token (phone, token)
            VALUES (:phone, :token)
            """
            
            # Ensure token is a valid JSON format (serializing to JSON)
            token_json = json.dumps(response.json())  # Use .json() for structured response
            
            # Execute the insert query
            await database.execute(query=query_insert, values={"phone": phone_agent, "token": token_json})
            
            # Return success response
            return {"status": "ok", "token": eval(token_json)}
    
    except requests.exceptions.RequestException as req_error:
        print(req_error)
        # Handle any network/HTTP request-related exceptions
        raise HTTPException(status_code=500, detail=f"Request error: {str(req_error)}")
    
    except Exception as error:
        print(error)
        # Catch any other unexpected errors (e.g., database errors)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(error)}")


async def handle_get_events(phone_agent: str,min_start_time,max_start_time, settings=Depends(get_settings)):
    # Define the URL and data for the POST request
    url = 'https://auth.calendly.com/oauth/token'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}'
    }
    try:
        query = f"SELECT * FROM manage_token WHERE phone='{phone_agent}'"
        results = await database.fetch_all(query=query)
        if(len(results) > 0 ):
            token_data = eval(results[0]['token'])
            expired_time = token_data['created_at'] + token_data['expires_in']
            if(expired_time > int(time.time())):
                print("not expired ....")
            else:
                print("resfresh token")
                data_refresh = {
                    'grant_type': 'refresh_token',
                    'refresh_token': token_data['refresh_token'] 
                }
                response = requests.post(url, data=data_refresh, headers=headers)
                # Check if the response is successful
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"Error from Calendly API: {response.text}")

                # Perform database operations
                query_delete = "DELETE FROM manage_token WHERE phone = :phone"
                await database.fetch_all(query=query_delete, values={"phone": phone_agent})

                query_insert = """
                INSERT INTO manage_token (phone, token)
                VALUES (:phone, :token)
                """
                
                # Ensure token is a valid JSON format (serializing to JSON)
                token_json = json.dumps(response.json())  # Use .json() for structured response
                
                # Execute the insert query
                await database.execute(query=query_insert, values={"phone": phone_agent, "token": token_json})
                print("token_json refresh...", token_json)
                # Return success response
                token_data = eval(token_json)
                # return {"status": "ok", "token": eval(token_json)}
            
            # infor user
            url_me = "https://api.calendly.com/users/me"
            headers =  {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Bearer {token_data["access_token"]}'
            }
            # Make the GET request to the Calendly API
            response = requests.get(url_me, headers=headers)
            user_data = response.json()
            user_data = user_data["resource"]
            
            # list event 
            url_event = f"https://api.calendly.com/scheduled_events?organization={user_data['current_organization']}&user={user_data['uri']}&count=100"
            if(min_start_time != None):
                url_event = f"{url_event}&min_start_time={min_start_time}"
            if(max_start_time != None):
                url_event = f"{url_event}&max_start_time={max_start_time}"
                
            print("url_event",url_event)
            response = requests.get(url_event, headers=headers)
            events_data = response.json()
            
            return {"status":"ok","token":token_data, "user_data":user_data, "events_data":events_data }   
        else:
           return {"status":"failed","message":"no token for this user"}
        
            
    except Exception as error:
        print(error)
    
async def handle_get_user_availability_schedules(phone_agent: str, settings=Depends(get_settings)):
    
    # Define the URL and data for the POST request
    url = 'https://auth.calendly.com/oauth/token'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}'
    }
    try:
        query = f"SELECT * FROM manage_token WHERE phone='{phone_agent}'"
        results = await database.fetch_all(query=query)
        if(len(results) > 0 ):
            token_data = eval(results[0]['token'])
            expired_time = token_data['created_at'] + token_data['expires_in']
            if(expired_time > int(time.time())):
                print("not expired ....")
            else:
                print("resfresh token")
                data_refresh = {
                    'grant_type': 'refresh_token',
                    'refresh_token': token_data['refresh_token'] 
                }
                response = requests.post(url, data=data_refresh, headers=headers)
                # Check if the response is successful
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"Error from Calendly API: {response.text}")

                # Perform database operations
                query_delete = "DELETE FROM manage_token WHERE phone = :phone"
                await database.fetch_all(query=query_delete, values={"phone": phone_agent})

                query_insert = """
                INSERT INTO manage_token (phone, token)
                VALUES (:phone, :token)
                """
                
                # Ensure token is a valid JSON format (serializing to JSON)
                token_json = json.dumps(response.json())  # Use .json() for structured response
                
                # Execute the insert query
                await database.execute(query=query_insert, values={"phone": phone_agent, "token": token_json})
                print("token_json refresh...", token_json)
                # Return success response
                token_data = eval(token_json)
                # return {"status": "ok", "token": eval(token_json)}
            
            # infor user
            url_me = "https://api.calendly.com/users/me"
            headers =  {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Bearer {token_data["access_token"]}'
            }
            # Make the GET request to the Calendly API
            response = requests.get(url_me, headers=headers)
            user_data = response.json()
            user_data = user_data["resource"]
            
            # list event 
            url_availability = f"https://api.calendly.com/user_availability_schedules?user={user_data['uri']}"
         
                
            print("url_availability",url_availability)
            response = requests.get(url_availability, headers=headers)
            availability_data = response.json()
            
            return {"status":"ok","token":token_data, "user_data":user_data, "availability_data":availability_data }   
        else:
           return {"status":"failed","message":"no token for this user"}
            
    except Exception as error:
        print(error)
        
        
async def handle_get_event_types(phone_agent: str, settings=Depends(get_settings)):
    
    # Define the URL and data for the POST request
    url = 'https://auth.calendly.com/oauth/token'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}'
    }
    try:
        query = f"SELECT * FROM manage_token WHERE phone='{phone_agent}'"
        results = await database.fetch_all(query=query)
        if(len(results) > 0 ):
            token_data = eval(results[0]['token'])
            expired_time = token_data['created_at'] + token_data['expires_in']
            if(expired_time > int(time.time())):
                print("not expired ....")
            else:
                print("resfresh token")
                data_refresh = {
                    'grant_type': 'refresh_token',
                    'refresh_token': token_data['refresh_token'] 
                }
                response = requests.post(url, data=data_refresh, headers=headers)
                # Check if the response is successful
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"Error from Calendly API: {response.text}")

                # Perform database operations
                query_delete = "DELETE FROM manage_token WHERE phone = :phone"
                await database.fetch_all(query=query_delete, values={"phone": phone_agent})

                query_insert = """
                INSERT INTO manage_token (phone, token)
                VALUES (:phone, :token)
                """
                
                # Ensure token is a valid JSON format (serializing to JSON)
                token_json = json.dumps(response.json())  # Use .json() for structured response
                
                # Execute the insert query
                await database.execute(query=query_insert, values={"phone": phone_agent, "token": token_json})
                print("token_json refresh...", token_json)
                # Return success response
                token_data = eval(token_json)
                # return {"status": "ok", "token": eval(token_json)}
            
            # infor user
            url_me = "https://api.calendly.com/users/me"
            headers =  {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Bearer {token_data["access_token"]}'
            }
            # Make the GET request to the Calendly API
            response = requests.get(url_me, headers=headers)
            user_data = response.json()
            user_data = user_data["resource"]
            
            # list event 
            url_event_types = f"https://api.calendly.com/event_types?active=true&organization={user_data['current_organization']}"     
            # print("event_types",url_event_types)
            response = requests.get(url_event_types, headers=headers)
            event_types_data = response.json()
            
            return {"status":"ok","token":token_data, "user_data":user_data, "event_types":event_types_data }   
        else:
           return {"status":"failed","message":"no token for this user"}
        
            
    except Exception as error:
        print(error)