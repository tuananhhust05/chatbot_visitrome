from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import asyncio
import json
from typing import List, Dict, Optional
from databases import Database
from dotenv import load_dotenv
import weaviate
from sentence_transformers import SentenceTransformer
import logging

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["Database Management"])

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
WEAVIATE_DEFAULT_PROPERTIES = ["category", "content", "url", "doc_id", "chunk_id", "agentId"]
WEAVIATE_BATCH_SIZE = 100
WEAVIATE_EMBEDDING_MODEL = SentenceTransformer('all-distilroberta-v1')
WEAVIATE_CLASS_HOTELS = "Hotels"
WEAVIATE_CLASS_TOURS = "Tours"

# Pydantic models for request validation
class QueryRequest(BaseModel):
    query: str
    description: str = "Custom SQL query"

class QueryResponse(BaseModel):
    success: bool
    message: str
    data: dict

# Database connection parameters
POSTGRES_PORT = os.getenv("POSTGRES_PORT_AGENT_PRIVATE", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB_AGENT", "agent_db")
POSTGRES_USER = os.getenv("POSTGRES_USER_AGENT", "myuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD_AGENT", "mypassword")
POSTGRES_HOST = os.getenv("POSTGRES_HOST_AGENT", "localhost")

# Create database URL
DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

def normalize_class_name(class_name: str) -> str:
    mapping = {
        "hotels": WEAVIATE_CLASS_HOTELS,
        "hotel": WEAVIATE_CLASS_HOTELS,
        WEAVIATE_CLASS_HOTELS.lower(): WEAVIATE_CLASS_HOTELS,
        "tours": WEAVIATE_CLASS_TOURS,
        "tour": WEAVIATE_CLASS_TOURS,
        WEAVIATE_CLASS_TOURS.lower(): WEAVIATE_CLASS_TOURS,
    }
    if not class_name:
        return class_name
    return mapping.get(class_name.lower(), class_name)


async def get_database():
    """Get database connection"""
    database = Database(DATABASE_URL)
    await database.connect()
    try:
        yield database
    finally:
        await database.disconnect()

def fetch_weaviate_class_data(
    client: weaviate.Client,
    class_name: str,
    properties: Optional[List[str]] = None,
    batch_size: int = WEAVIATE_BATCH_SIZE,
    max_items: Optional[int] = None,
):
    """Retrieve entire dataset for a given Weaviate class with pagination."""
    class_key = normalize_class_name(class_name)
    props = properties or WEAVIATE_DEFAULT_PROPERTIES
    results: List[Dict] = []
    offset = 0
    remaining = max_items

    while True:
        current_limit = batch_size if remaining is None else min(batch_size, max(remaining, 0))
        if current_limit <= 0:
            break
        response = (
            client.query
            .get(class_key, props)
            .with_limit(current_limit)
            .with_offset(offset)
            .with_additional(["id"])
            .do()
        )
        items = response.get("data", {}).get("Get", {}).get(class_key, []) or []
        if not items:
            break
        results.extend(items)
        if remaining is not None:
            remaining -= len(items)
        if remaining is not None and remaining <= 0:
            break
        if len(items) < current_limit:
            break
        offset += current_limit

    return results


def format_weaviate_record(record: Dict) -> Dict:
    payload = record.get("content")
    parsed_content = None
    if payload:
        try:
            parsed_content = json.loads(payload)
            if isinstance(parsed_content, str):
                parsed_content = json.loads(parsed_content)
        except Exception:
            parsed_content = payload

    return {
        "id": record.get("_additional", {}).get("id"),
        "properties": record,
        "content_parsed": parsed_content,
    }


def search_weaviate_class(
    client: weaviate.Client,
    class_name: str,
    vector: List[float],
    limit: int,
    agent_id: Optional[str] = None,
):
    class_key = normalize_class_name(class_name)
    query = client.query.get(class_key, WEAVIATE_DEFAULT_PROPERTIES)
    if agent_id:
        query = query.with_where({
            "path": ["agentId"],
            "operator": "Equal",
            "valueString": agent_id,
        })
    response = (
        query
        .with_near_vector({"vector": vector})
        .with_limit(limit)
        .with_additional(["id", "score", "distance"])
        .do()
    )
    return response.get("data", {}).get("Get", {}).get(class_key, []) or []


@router.get("/weaviate-data")
async def get_weaviate_collections_data(limit: int = 1000):
    """
    Fetch all documents from Weaviate classes `hotels` and `tours`.

    Args:
        limit: Maximum number of records per class (capped by WEAVIATE_BATCH_SIZE).
    """
    try:
        client = weaviate.Client(WEAVIATE_URL)
        batch_size = min(limit, WEAVIATE_BATCH_SIZE)

        hotels = fetch_weaviate_class_data(
            client,
            WEAVIATE_CLASS_HOTELS,
            WEAVIATE_DEFAULT_PROPERTIES,
            batch_size=batch_size,
            max_items=limit,
        )
        tours = fetch_weaviate_class_data(
            client,
            WEAVIATE_CLASS_TOURS,
            WEAVIATE_DEFAULT_PROPERTIES,
            batch_size=batch_size,
            max_items=limit,
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Weaviate data fetched successfully",
                "data": {
                    "hotels_count": len(hotels),
                    "tours_count": len(tours),
                    "hotels": hotels,
                    "tours": tours,
                },
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Failed to fetch Weaviate data: {str(e)}",
                "error": str(e),
            },
        )

@router.post("/execute-sql-file")
async def execute_sql_file(
    sql_filename: str,
    database: Database = Depends(get_database)
):
    """
    Execute SQL file from the agentsupporter directory
    
    Args:
        sql_filename: Name of the SQL file to execute (e.g., 'backupagent.sql')
    """
    try:
        # Construct the full path to the SQL file
        sql_file_path = os.path.join(os.getcwd(), sql_filename)
        
        # Check if file exists
        if not os.path.exists(sql_file_path):
            raise HTTPException(
                status_code=404, 
                detail=f"SQL file '{sql_filename}' not found at path: {sql_file_path}"
            )
        
        # Read SQL file content
        with open(sql_file_path, 'r', encoding='utf-8') as sql_file:
            sql_content = sql_file.read()
        
        # Split SQL content by semicolon to handle multiple statements
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        executed_statements = 0
        errors = []
        
        # Execute each SQL statement
        for i, statement in enumerate(sql_statements):
            try:
                # Skip comments and empty statements
                if statement.startswith('--') or not statement:
                    continue
                    
                await database.execute(statement)
                executed_statements += 1
                print(f"✅ Executed statement {i+1}/{len(sql_statements)}")
                
            except Exception as e:
                error_msg = f"Error in statement {i+1}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
                # Continue with other statements even if one fails
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"SQL file '{sql_filename}' executed successfully",
                "data": {
                    "file_path": sql_file_path,
                    "total_statements": len(sql_statements),
                    "executed_statements": executed_statements,
                    "errors": errors,
                    "has_errors": len(errors) > 0
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute SQL file: {str(e)}"
        )

@router.post("/execute-backup")
async def execute_backup_agent_sql(database: Database = Depends(get_database)):
    """
    Execute the backupagent.sql file specifically
    """
    return await execute_sql_file("backupagent.sql", database)

@router.get("/status")
async def get_database_status(database: Database = Depends(get_database)):
    """
    Get database connection status and basic info
    """
    try:
        # Test connection
        result = await database.fetch_one("SELECT 1 as test")
        
        # Get database info
        db_info = await database.fetch_one("SELECT current_database() as db_name, version() as version")
        
        # Get table count
        table_count = await database.fetch_one("""
            SELECT COUNT(*) as table_count 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Database connection successful",
                "data": {
                    "connection_test": result,
                    "database_name": db_info['db_name'],
                    "postgres_version": db_info['version'],
                    "table_count": table_count['table_count'],
                    "connection_url": DATABASE_URL.replace(POSTGRES_PASSWORD, "***")
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )

@router.get("/tables")
async def get_database_tables(database: Database = Depends(get_database)):
    """
    Get list of all tables in the database
    """
    try:
        tables = await database.fetch_all("""
            SELECT 
                table_name,
                table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Database tables retrieved successfully",
                "data": {
                    "tables": [dict(table) for table in tables],
                    "total_tables": len(tables)
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database tables: {str(e)}"
        )

@router.post("/execute-query")
async def execute_custom_query(
    query_request: QueryRequest,
    database: Database = Depends(get_database)
):
    """
    Execute any custom SQL query
    
    Args:
        query_request: Object containing the SQL query and description
    """
    try:
        query = query_request.query.strip()
        
        if not query:
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )
        
        # Security check - prevent dangerous operations
        dangerous_keywords = [
            'DROP DATABASE', 'DROP SCHEMA', 'TRUNCATE', 'DELETE FROM',
            'ALTER SYSTEM', 'CREATE USER', 'DROP USER', 'GRANT', 'REVOKE'
        ]
        
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise HTTPException(
                    status_code=403,
                    detail=f"Operation '{keyword}' is not allowed for security reasons"
                )
        
        # Determine query type and execute accordingly
        if query_upper.startswith('SELECT') or query_upper.startswith('WITH'):
            # SELECT query - fetch data
            result = await database.fetch_all(query)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Query executed successfully",
                    "data": {
                        "query": query,
                        "description": query_request.description,
                        "query_type": "SELECT",
                        "result": [dict(row) for row in result],
                        "row_count": len(result)
                    }
                }
            )
        else:
            # INSERT, UPDATE, CREATE, etc. - execute without returning data
            result = await database.execute(query)
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Query executed successfully",
                    "data": {
                        "query": query,
                        "description": query_request.description,
                        "query_type": "MODIFY",
                        "affected_rows": result if isinstance(result, int) else "Unknown"
                    }
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute query: {str(e)}"
        )

@router.post("/execute-raw-query")
async def execute_raw_query(
    query: str = Body(..., embed=True),
    database: Database = Depends(get_database)
):
    """
    Execute raw SQL query (alternative endpoint with simpler input)
    
    Args:
        query: Raw SQL query string
    """
    query_request = QueryRequest(query=query, description="Raw SQL query")
    return await execute_custom_query(query_request, database)

@router.get("/query-examples")
async def get_query_examples():
    """
    Get examples of common SQL queries
    """
    examples = {
        "select_examples": [
            {
                "description": "Get all tables",
                "query": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            },
            {
                "description": "Get table structure",
                "query": "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'your_table_name'"
            },
            {
                "description": "Count records in table",
                "query": "SELECT COUNT(*) as total_records FROM your_table_name"
            }
        ],
        "insert_examples": [
            {
                "description": "Insert new record",
                "query": "INSERT INTO your_table_name (column1, column2) VALUES ('value1', 'value2')"
            }
        ],
        "update_examples": [
            {
                "description": "Update record",
                "query": "UPDATE your_table_name SET column1 = 'new_value' WHERE id = 1"
            }
        ],
        "create_examples": [
            {
                "description": "Create new table",
                "query": "CREATE TABLE new_table (id SERIAL PRIMARY KEY, name VARCHAR(100))"
            }
        ]
    }
    
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": "Query examples retrieved successfully",
            "data": examples
        }
    )

@router.post("/create-weaviate-class")
async def create_weaviate_class():
    """
    Create SupportAgent class in Weaviate
    """
    try:
        import weaviate
        
        # Connect to Weaviate
        client = weaviate.Client(WEAVIATE_URL)
        
        # Check if class already exists
        if client.schema.contains({"classes": [{"class": "SupportAgent"}]}):
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "SupportAgent class already exists in Weaviate",
                    "data": {
                        "class_name": "SupportAgent",
                        "status": "already_exists"
                    }
                }
            )
        
        # Define class schema (from createClass.py)
        class_obj = {
            "class": "SupportAgent",
            "description": "A class to store content for agents",
            "vectorizer": "text2vec-openai",  
            "moduleConfig": {
                "text2vec-openai": {
                    "vectorizeClassName": False
                }
            },
            "properties": [
                {
                    "name": "category",
                    "dataType": ["text"]
                },
                {
                    "name": "content",
                    "dataType": ["text"]
                },
                {
                    "name": "url",
                    "dataType": ["text"]
                },
                {
                    "name": "doc_id",
                    "dataType": ["text"]
                },
                {
                    "name": "chunk_id",
                    "dataType": ["text"]
                },
                {
                    "name": "agentId",
                    "dataType": ["text"]
                }
            ]
        }
        
        # Create class in schema
        client.schema.create_class(class_obj)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "SupportAgent class created successfully in Weaviate",
                "data": {
                    "class_name": "SupportAgent",
                    "status": "created",
                    "schema": class_obj
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Failed to create Weaviate class: {str(e)}",
                "error": str(e)
            }
        )

@router.get("/weaviate-status")
async def get_weaviate_status():
    """
    Check Weaviate connection and class status
    """
    try:
        import weaviate
        
        # Connect to Weaviate
        client = weaviate.Client("http://weaviate:8080")
        
        # Get schema
        schema = client.schema.get()
        
        # Check if SupportAgent class exists
        support_agent_exists = client.schema.contains({"classes": [{"class": "SupportAgent"}]})
        
        # Get all classes
        all_classes = [cls["class"] for cls in schema.get("classes", [])]
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Weaviate status retrieved successfully",
                "data": {
                    "connection": "success",
                    "support_agent_exists": support_agent_exists,
                    "all_classes": all_classes,
                    "total_classes": len(all_classes)
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Failed to connect to Weaviate: {str(e)}",
                "error": str(e)
            }
        )

@router.delete("/delete-weaviate-class")
async def delete_weaviate_class(class_name: str):
    """
    Delete specified class from Weaviate.
    """
    try:
        client = weaviate.Client(WEAVIATE_URL)

        if not class_name or not class_name.strip():
            raise HTTPException(status_code=400, detail="class_name must not be empty")

        if not client.schema.contains({"classes": [{"class": class_name}]}):
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": f"{class_name} class does not exist in Weaviate",
                    "data": {
                        "class_name": class_name,
                        "status": "not_found"
                    }
                }
            )

        client.schema.delete_class(class_name)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"{class_name} class deleted successfully from Weaviate",
                "data": {
                    "class_name": class_name,
                    "status": "deleted"
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Failed to delete Weaviate class: {str(e)}",
                "error": str(e)
            }
        )

@router.post("/setup-checkpointer")
async def setup_checkpointer():
    """
    Setup LangGraph PostgresSaver checkpointer tables
    """
    try:
        import os
        from psycopg_pool import AsyncConnectionPool
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        
        # Database connection settings
        POSTGRES_PORT = os.getenv("POSTGRES_PORT_AGENT_PRIVATE", "5432")
        POSTGRES_DB = os.getenv("POSTGRES_DB_AGENT", "agent_db")
        POSTGRES_USER = os.getenv("POSTGRES_USER_AGENT", "myuser")
        POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD_AGENT", "mypassword")
        POSTGRES_HOST = os.getenv("POSTGRES_HOST_AGENT", "localhost")
        
        DATABASE_URL = (
            f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
            f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )
        
        connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
        }
        
        # Create connection pool
        async with AsyncConnectionPool(
            conninfo=DATABASE_URL,
            min_size=1, 
            max_size=2,
            max_lifetime=120,
            max_idle=60,
            kwargs=connection_kwargs
        ) as pool:
            
            # Create checkpointer
            checkpointer = AsyncPostgresSaver(pool)
            
            # Setup checkpointer tables
            await checkpointer.setup()
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "LangGraph PostgresSaver checkpointer setup completed successfully",
                    "data": {
                        "database_url": DATABASE_URL.replace(POSTGRES_PASSWORD, "***"),
                        "tables_created": [
                            "checkpoints",
                            "checkpoint_writes", 
                            "checkpoint_blobs",
                            "checkpoint_migrations"
                        ],
                        "status": "setup_completed"
                    }
                }
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Failed to setup checkpointer: {str(e)}",
                "error": str(e)
            }
        )

@router.get("/checkpointer-status")
async def get_checkpointer_status():
    """
    Check LangGraph PostgresSaver checkpointer tables status
    """
    try:
        import os
        from psycopg_pool import AsyncConnectionPool
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        
        # Database connection settings
        POSTGRES_PORT = os.getenv("POSTGRES_PORT_AGENT_PRIVATE", "5432")
        POSTGRES_DB = os.getenv("POSTGRES_DB_AGENT", "agent_db")
        POSTGRES_USER = os.getenv("POSTGRES_USER_AGENT", "myuser")
        POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD_AGENT", "mypassword")
        POSTGRES_HOST = os.getenv("POSTGRES_HOST_AGENT", "localhost")
        
        DATABASE_URL = (
            f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
            f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )
        
        connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
        }
        
        # Create connection pool
        async with AsyncConnectionPool(
            conninfo=DATABASE_URL,
            min_size=1, 
            max_size=2,
            max_lifetime=120,
            max_idle=60,
            kwargs=connection_kwargs
        ) as pool:
            
            # Check if tables exist
            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    # Check checkpoint tables
                    await cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name LIKE 'checkpoint%'
                        ORDER BY table_name
                    """)
                    tables = await cur.fetchall()
                    table_names = [row[0] for row in tables]
                    
                    # Check checkpoint_migrations data
                    await cur.execute("SELECT * FROM checkpoint_migrations")
                    migrations = await cur.fetchall()
                    
                    # Check constraints
                    await cur.execute("""
                        SELECT 
                            tc.table_name, 
                            tc.constraint_name, 
                            tc.constraint_type,
                            string_agg(kcu.column_name, ', ') as columns
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu 
                            ON tc.constraint_name = kcu.constraint_name
                        WHERE tc.table_name LIKE 'checkpoint%'
                        GROUP BY tc.table_name, tc.constraint_name, tc.constraint_type
                        ORDER BY tc.table_name, tc.constraint_type
                    """)
                    constraints = await cur.fetchall()
                    
                    return JSONResponse(
                        status_code=200,
                        content={
                            "success": True,
                            "message": "Checkpointer status retrieved successfully",
                            "data": {
                                "database_url": DATABASE_URL.replace(POSTGRES_PASSWORD, "***"),
                                "tables_found": table_names,
                                "tables_count": len(table_names),
                                "migrations_data": [{"version": row[0]} for row in migrations],
                                "constraints": [
                                    {
                                        "table": row[0],
                                        "constraint": row[1], 
                                        "type": row[2],
                                        "columns": row[3]
                                    } for row in constraints
                                ],
                                "status": "ready" if len(table_names) >= 4 else "incomplete"
                            }
                        }
                    )
                    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Failed to check checkpointer status: {str(e)}",
                "error": str(e)
            }
        )

@router.post("/insert-hotels")
async def insert_hotels_to_weaviate(hotels: List[Dict] = Body(...)):
    """
    Insert hotel data into Weaviate class "hotels".
    Stringify JSON and save to "content" field following the class structure.
    
    Args:
        hotels: List of hotel objects with fields: id, city, country, name, price_range, des
    """
    try:
        # Connect to Weaviate
        weaviate_client = weaviate.Client("http://weaviate:8080")
        logger.info("✓ Connected to Weaviate")
        
        # Initialize embedding model
        embedding_model = SentenceTransformer('all-distilroberta-v1')
        logger.info("✓ Loaded embedding model")
        
        # Insert hotels
        inserted_count = 0
        failed_count = 0
        errors = []
        
        for hotel in hotels:
            try:
                # Prepare hotel data with defaults
                hotel_id = hotel.get('id', 'unknown')
                city = hotel.get('city', '')
                country = hotel.get('country', '')
                name = hotel.get('name', '')
                price_range = hotel.get('price_range', '')
                description = hotel.get('des', '')
                
                # Stringify the entire hotel JSON and save to "content" field
                hotel_json_string = json.dumps(hotel, ensure_ascii=False)
                
                # Create content string for embedding (combine all fields for better search)
                content_for_embedding = f"{name}. {description}. Located in {city}, {country}. Price: {price_range}"
                
                # Generate embedding from content
                vector = embedding_model.encode(content_for_embedding)
                
                # Prepare properties following the class structure: category, content, url, doc_id, chunk_id, agentId
                properties = {
                    "category": "hotel",  # Default category
                    "content": hotel_json_string,  # Stringified JSON
                    "url": hotel.get('url', ''),  # URL if exists, otherwise empty
                    "doc_id": str(hotel_id),  # Hotel ID
                    "chunk_id": "0",  # Default chunk_id since we don't chunk
                    "agentId": "1"  # Default agentId
                }
                
                # Insert into Weaviate class "hotels"
                weaviate_client.data_object.create(
                    data_object=properties,
                    class_name=WEAVIATE_CLASS_HOTELS,
                    vector=vector.tolist()
                )
                print("inserted_count", inserted_count)
                
                inserted_count += 1
                
                if inserted_count % 10 == 0:
                    logger.info(f"  Inserted {inserted_count} hotels...")
                    
            except Exception as e:
                failed_count += 1
                error_msg = f"Failed to insert hotel {hotel.get('id', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Hotel data insertion completed",
                "data": {
                    "inserted_count": inserted_count,
                    "failed_count": failed_count,
                    "total_processed": len(hotels),
                    "errors": errors if errors else None,
                    "collection": "hotels"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error inserting hotels to Weaviate: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error inserting hotels to Weaviate: {str(e)}"
        )

@router.post("/insert-tours")
async def insert_tours_to_weaviate(tours: List[Dict] = Body(...)):
    """
    Insert tour data into Weaviate class "tours".
    Stringify JSON and save to "content" field following the class structure.
    
    Args:
        tours: List of tour objects with fields: tour_id, tour_name, country, city, provider, items
    """
    try:
        # Connect to Weaviate
        weaviate_client = weaviate.Client("http://weaviate:8080")
        logger.info("✓ Connected to Weaviate")
        
        # Initialize embedding model
        embedding_model = SentenceTransformer('all-distilroberta-v1')
        logger.info("✓ Loaded embedding model")
        
        # Insert tours
        inserted_count = 0
        failed_count = 0
        errors = []
        
        for tour in tours:
            try:
                # Prepare tour data with defaults
                tour_id = tour.get('tour_id', 'unknown')
                tour_name = tour.get('tour_name', '')
                city = tour.get('city', '')
                country = tour.get('country', '')
                provider = tour.get('provider', {})
                provider_name = provider.get('name', '') if isinstance(provider, dict) else ''
                provider_website = provider.get('website', '') if isinstance(provider, dict) else ''
                items = tour.get('items', [])
                
                # Stringify the entire tour JSON and save to "content" field
                tour_json_string = json.dumps(tour, ensure_ascii=False)
                
                # Create content string for embedding (combine all fields for better search)
                items_summary = ', '.join([item.get('location_name', '') for item in items if isinstance(item, dict)])
                content_for_embedding = f"{tour_name}. {provider_name}. Located in {city}, {country}. Locations: {items_summary}"
                
                # Generate embedding from content
                vector = embedding_model.encode(content_for_embedding)
                
                # Prepare properties following the class structure: category, content, url, doc_id, chunk_id, agentId
                properties = {
                    "category": "tour",  # Default category
                    "content": tour_json_string,  # Stringified JSON
                    "url": provider_website or '',  # Provider website if exists, otherwise empty
                    "doc_id": str(tour_id),  # Tour ID
                    "chunk_id": "0",  # Default chunk_id since we don't chunk
                    "agentId": "1"  # Default agentId
                }
                
                # Insert into Weaviate class "tours"
                weaviate_client.data_object.create(
                    data_object=properties,
                    class_name=WEAVIATE_CLASS_TOURS,
                    vector=vector.tolist()
                )
                
                inserted_count += 1
                
                if inserted_count % 10 == 0:
                    logger.info(f"  Inserted {inserted_count} tours...")
                    
            except Exception as e:
                failed_count += 1
                error_msg = f"Failed to insert tour {tour.get('tour_id', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Tour data insertion completed",
                "data": {
                    "inserted_count": inserted_count,
                    "failed_count": failed_count,
                    "total_processed": len(tours),
                    "errors": errors if errors else None,
                    "collection": "tours"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error inserting tours to Weaviate: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error inserting tours to Weaviate: {str(e)}"
        )

@router.post("/create-hotels-class")
async def create_hotels_class():
    """
    Create "hotels" class in Weaviate if it doesn't exist
    """
    try:
        # Connect to Weaviate
        client = weaviate.Client("http://weaviate:8080")
        
        # Check if class already exists
        if client.schema.contains({"classes": [{"class": WEAVIATE_CLASS_HOTELS}]}):
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "hotels class already exists in Weaviate",
                    "data": {
                        "class_name": WEAVIATE_CLASS_HOTELS,
                        "status": "already_exists"
                    }
                }
            )
        
        # Define hotels class schema aligned with insert payload
        class_obj = {
            "class": WEAVIATE_CLASS_HOTELS,
            "description": "A class to store hotel information",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "vectorizeClassName": False
                }
            },
            "properties": [
                {
                    "name": "category",
                    "dataType": ["text"]
                },
                {
                    "name": "content",
                    "dataType": ["text"]
                },
                {
                    "name": "url",
                    "dataType": ["text"]
                },
                {
                    "name": "doc_id",
                    "dataType": ["text"]
                },
                {
                    "name": "chunk_id",
                    "dataType": ["text"]
                },
                {
                    "name": "agentId",
                    "dataType": ["text"]
                }
            ]
        }
        
        # Create class in schema
        client.schema.create_class(class_obj)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "hotels class created successfully in Weaviate",
                "data": {
                    "class_name": WEAVIATE_CLASS_HOTELS,
                    "status": "created",
                    "schema": class_obj
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Failed to create hotels class: {str(e)}",
                "error": str(e)
            }
        )


@router.post("/create-tours-class")
async def create_tours_class():
    """
    Create "tours" class in Weaviate if it doesn't exist
    """
    try:
        client = weaviate.Client(WEAVIATE_URL)

        if client.schema.contains({"classes": [{"class": WEAVIATE_CLASS_TOURS}]}):
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "tours class already exists in Weaviate",
                    "data": {
                        "class_name": WEAVIATE_CLASS_TOURS,
                        "status": "already_exists"
                    }
                }
            )

        class_obj = {
            "class": WEAVIATE_CLASS_TOURS,
            "description": "A class to store tour information",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "vectorizeClassName": False
                }
            },
            "properties": [
                {
                    "name": "category",
                    "dataType": ["text"]
                },
                {
                    "name": "content",
                    "dataType": ["text"]
                },
                {
                    "name": "url",
                    "dataType": ["text"]
                },
                {
                    "name": "doc_id",
                    "dataType": ["text"]
                },
                {
                    "name": "chunk_id",
                    "dataType": ["text"]
                },
                {
                    "name": "agentId",
                    "dataType": ["text"]
                }
            ]
        }

        client.schema.create_class(class_obj)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "tours class created successfully in Weaviate",
                "data": {
                    "class_name": WEAVIATE_CLASS_TOURS,
                    "status": "created",
                    "schema": class_obj
                }
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Failed to create tours class: {str(e)}",
                "error": str(e)
            }
        )
