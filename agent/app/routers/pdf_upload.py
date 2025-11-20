from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import os
import shutil
from pathlib import Path
from typing import List, Dict
import re
import weaviate
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="app/views")

router = APIRouter(
    prefix="/rag",
    tags=["pdf-upload"],
)

# Configuration
UPLOAD_DIR = "uploads"
WEAVIATE_COLLECTION = "SupportAgent"
ALLOWED_EXTENSIONS = {".pdf"}

def ensure_upload_dir():
    """Ensure upload directory exists"""
    Path(UPLOAD_DIR).mkdir(exist_ok=True)

def is_valid_pdf(filename: str) -> bool:
    """Check if file is a valid PDF"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def read_pdf_content(pdf_path: str) -> str:
    """
    Read and extract text content from PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    try:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        reader = PdfReader(pdf_path)
        logger.info(f"✓ Successfully loaded PDF: {os.path.basename(pdf_path)}")
        logger.info(f"  Pages: {len(reader.pages)}")
        
        # Extract text from all pages
        text_content = ""
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    text_content += page_text + "\n"
            except Exception as e:
                logger.warning(f"Warning: Could not extract text from page {page_num + 1}: {e}")
        
        return text_content.strip()
        
    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using regex pattern.
    
    Args:
        text (str): Input text
        
    Returns:
        List[str]: List of sentences
    """
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split by sentence endings (., !, ?) followed by space or end of string
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Filter out empty sentences and clean up
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences

def process_pdf_data(pdf_path: str, doc_id: int = 1) -> List[Dict]:
    """
    Process PDF file and create chunks for Weaviate insertion.
    
    Args:
        pdf_path (str): Path to the PDF file
        doc_id (int): Document ID for the PDF
        
    Returns:
        List[Dict]: List of chunked data ready for Weaviate
    """
    # Read PDF content
    pdf_content = read_pdf_content(pdf_path)
    if not pdf_content:
        raise HTTPException(status_code=400, detail="Failed to read PDF content")
    
    logger.info(f"✓ Extracted {len(pdf_content)} characters from PDF")
    
    # Split into sentences first
    sentences = split_into_sentences(pdf_content)
    logger.info(f"✓ Split into {len(sentences)} sentences")
    
    # Create chunks from sentences
    chunked_data = []
    
    # Process each sentence as a separate chunk
    for i, sentence in enumerate(sentences):
        if len(sentence.strip()) > 10:  # Only include meaningful sentences
            chunked_data.append({
                'id': doc_id,
                'url': "",  # Empty string as requested
                'chunk_id': i,
                'total_chunks': len(sentences),
                'category': "",  # Empty string as requested
                'content': sentence.strip()
            })
    
    logger.info(f"✓ Created {len(chunked_data)} chunks for Weaviate insertion")
    return chunked_data

def clear_weaviate_collection(collection_name: str = WEAVIATE_COLLECTION):
    """
    Delete and recreate Weaviate collection to clear all data.
    
    Args:
        collection_name (str): Name of the collection to clear
    """
    try:
        # weaviate_client = weaviate.Client("http://localhost:8080")
        weaviate_client = weaviate.Client("http://weaviate:8080")
        
        # Check if collection exists and delete it
        try:
            # Delete the entire collection using old API
            weaviate_client.schema.delete_class(collection_name)
            logger.info(f"✓ Deleted collection: {collection_name}")
        except Exception as e:
            logger.info(f"Collection {collection_name} does not exist or already deleted: {e}")
        
        # Create new collection with the same schema
        class_obj = {
            "class": collection_name,
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
        
        # Create the new collection
        weaviate_client.schema.create_class(class_obj)
        logger.info(f"✓ Recreated collection: {collection_name}")
        
    except Exception as e:
        logger.error(f"Error recreating Weaviate collection: {e}")
        raise HTTPException(status_code=500, detail=f"Error recreating Weaviate collection: {str(e)}")

def insert_to_weaviate(chunked_data: List[Dict], collection_name: str = WEAVIATE_COLLECTION):
    """
    Insert chunked data into Weaviate collection.
    
    Args:
        chunked_data (List[Dict]): Data to insert
        collection_name (str): Name of the Weaviate collection
    """
    try:
        # Connect to Weaviate using Client
        # weaviate_client = weaviate.Client("http://localhost:8080")
        weaviate_client = weaviate.Client("http://weaviate:8080")
        logger.info("✓ Connected to Weaviate")
        
        # Initialize embedding model
        embedding_model = SentenceTransformer('all-distilroberta-v1')
        logger.info("✓ Loaded embedding model")
        
        # Insert data
        inserted_count = 0
        for item in chunked_data:
            try:
                # Generate embedding
                vector = embedding_model.encode(item['content'])
                
                # Prepare properties
                properties = {
                    "doc_id": str(item['id']),  # Convert to string
                    "url": item['url'],
                    "chunk_id": str(item['chunk_id']),  # Convert to string
                    "category": item['category'],
                    "content": item['content'],
                    "agentId": "1"
                }
                print(properties)
                # Add object with custom vector using the old API
                weaviate_client.data_object.create(
                    data_object=properties,
                    class_name=collection_name,
                    vector=vector.tolist()
                )
                inserted_count += 1
                
                if inserted_count % 10 == 0:
                    logger.info(f"  Inserted {inserted_count} chunks...")
                    
            except Exception as e:
                logger.warning(f"Warning: Failed to insert chunk {item['chunk_id']}: {e}")
        
        logger.info(f"✓ Successfully inserted {inserted_count} chunks into Weaviate")
        return inserted_count
        
    except Exception as e:
        logger.error(f"Error connecting to Weaviate: {e}")
        raise HTTPException(status_code=500, detail=f"Error connecting to Weaviate: {str(e)}")

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload PDF file, process content, and insert into Weaviate.
    
    Args:
        file (UploadFile): PDF file to upload
        
    Returns:
        JSONResponse: Processing results
    """
    try:
        # Ensure upload directory exists
        ensure_upload_dir()
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not is_valid_pdf(file.filename):
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")
        
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"✓ File saved to: {file_path}")
        
        # Process PDF data
        chunked_data = process_pdf_data(file_path, doc_id=1)
        
        if not chunked_data:
            raise HTTPException(status_code=400, detail="No content extracted from PDF")
        
        # Clear existing data from Weaviate collection
        clear_weaviate_collection()
        
        # Insert new data into Weaviate
        inserted_count = insert_to_weaviate(chunked_data)
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
            logger.info(f"✓ Cleaned up uploaded file: {file_path}")
        except Exception as e:
            logger.warning(f"Warning: Could not delete uploaded file: {e}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "PDF processed and inserted into Weaviate successfully",
                "data": {
                    "filename": file.filename,
                    "total_sentences": len(chunked_data),
                    "inserted_chunks": inserted_count,
                    "collection": WEAVIATE_COLLECTION
                }
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/status")
async def get_status():
    """
    Get status of PDF processing service.
    
    Returns:
        JSONResponse: Service status
    """
    try:
        # Check if Weaviate is accessible
        # weaviate_client = weaviate.Client("http://localhost:8080")
        weaviate_client = weaviate.Client("http://weaviate:8080")
        
        # Check if collection exists
        schema = weaviate_client.schema.get()
        collection_exists = any(cls['class'] == WEAVIATE_COLLECTION for cls in schema['classes'])
        
        if collection_exists:
            # Get collection info
            collection_info = next(cls for cls in schema['classes'] if cls['class'] == WEAVIATE_COLLECTION)
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "healthy",
                    "weaviate_connected": True,
                    "collection": WEAVIATE_COLLECTION,
                    "collection_properties": [
                        {"name": prop['name'], "type": prop['dataType'][0]} 
                        for prop in collection_info['properties']
                    ]
                }
            )
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "healthy",
                    "weaviate_connected": True,
                    "collection": WEAVIATE_COLLECTION,
                    "collection_properties": [],
                    "message": "Collection does not exist yet"
                }
            )
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "weaviate_connected": False,
                "error": str(e)
            }
        )

@router.get("/upload-page")
async def upload_page(request: Request):
    """
    Render the PDF upload page.
    
    Args:
        request (Request): FastAPI request object
        
    Returns:
        TemplateResponse: HTML page for PDF upload
    """
    return templates.TemplateResponse("pdf_upload.html", {"request": request})
