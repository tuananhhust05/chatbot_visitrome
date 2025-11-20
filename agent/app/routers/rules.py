from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from database.db import database
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules", tags=["Rules"])

# Pydantic models for request/response validation
class RuleCreate(BaseModel):
    content: str

class RuleUpdate(BaseModel):
    content: str

class RuleResponse(BaseModel):
    id: int
    content: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


def _format_error_detail(action: str, error: Exception) -> dict:
    """
    Build structured error details including traceback information.
    """
    return {
        "action": action,
        "error": str(error),
        "error_type": error.__class__.__name__,
        "traceback": traceback.format_exc(),
    }

@router.post("", response_model=RuleResponse)
async def create_rule(rule: RuleCreate):
    """
    Create a new rule
    
    - **content**: The content of the rule (required)
    """
    try:
        if not rule.content or not rule.content.strip():
            raise HTTPException(
                status_code=400,
                detail="Content cannot be empty"
            )
        
        query = """
            INSERT INTO rules (content, created_at, updated_at)
            VALUES (:content, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id, content, created_at, updated_at
        """
        
        result = await database.fetch_one(
            query=query,
            values={"content": rule.content}
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to create rule"
            )
        
        return {
            "id": result["id"],
            "content": result["content"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = _format_error_detail("create_rule", e)
        logger.error(f"Error creating rule: {error_detail}")
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )

@router.get("/getallrules", response_model=List[RuleResponse])
async def get_all_rules():
    """
    Get all rules
    """
    try:
        query = """
            SELECT id, content, created_at, updated_at
            FROM rules
            ORDER BY id DESC
        """
        
        results = await database.fetch_all(query=query)
        
        rules = []
        for result in results:
            rules.append({
                "id": result["id"],
                "content": result["content"],
                "created_at": str(result["created_at"]) if result["created_at"] else None,
                "updated_at": str(result["updated_at"]) if result["updated_at"] else None
            })
        
        return rules
        
    except Exception as e:
        error_detail = _format_error_detail("get_all_rules", e)
        logger.error(f"Error getting rules: {error_detail}")
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )

@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: int):
    """
    Get a specific rule by ID
    
    - **rule_id**: The ID of the rule to retrieve
    """
    try:
        query = """
            SELECT id, content, created_at, updated_at
            FROM rules
            WHERE id = :rule_id
        """
        
        result = await database.fetch_one(
            query=query,
            values={"rule_id": rule_id}
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Rule with ID {rule_id} not found"
            )
        
        return {
            "id": result["id"],
            "content": result["content"],
            "created_at": str(result["created_at"]) if result["created_at"] else None,
            "updated_at": str(result["updated_at"]) if result["updated_at"] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = _format_error_detail("get_rule", e)
        logger.error(f"Error getting rule: {error_detail}")
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )

@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: int, rule: RuleUpdate):
    """
    Update an existing rule
    
    - **rule_id**: The ID of the rule to update
    - **content**: The new content of the rule (required)
    """
    try:
        if not rule.content or not rule.content.strip():
            raise HTTPException(
                status_code=400,
                detail="Content cannot be empty"
            )
        
        # Check if rule exists
        check_query = "SELECT id FROM rules WHERE id = :rule_id"
        existing = await database.fetch_one(
            query=check_query,
            values={"rule_id": rule_id}
        )
        
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Rule with ID {rule_id} not found"
            )
        
        # Update rule
        update_query = """
            UPDATE rules
            SET content = :content, updated_at = CURRENT_TIMESTAMP
            WHERE id = :rule_id
            RETURNING id, content, created_at, updated_at
        """
        
        result = await database.fetch_one(
            query=update_query,
            values={
                "rule_id": rule_id,
                "content": rule.content
            }
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to update rule"
            )
        
        return {
            "id": result["id"],
            "content": result["content"],
            "created_at": str(result["created_at"]) if result["created_at"] else None,
            "updated_at": str(result["updated_at"]) if result["updated_at"] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = _format_error_detail("update_rule", e)
        logger.error(f"Error updating rule: {error_detail}")
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )

@router.delete("/{rule_id}")
async def delete_rule(rule_id: int):
    """
    Delete a rule by ID
    
    - **rule_id**: The ID of the rule to delete
    """
    try:
        # Check if rule exists
        check_query = "SELECT id FROM rules WHERE id = :rule_id"
        existing = await database.fetch_one(
            query=check_query,
            values={"rule_id": rule_id}
        )
        
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Rule with ID {rule_id} not found"
            )
        
        # Delete rule
        delete_query = "DELETE FROM rules WHERE id = :rule_id"
        await database.execute(
            query=delete_query,
            values={"rule_id": rule_id}
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Rule with ID {rule_id} deleted successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = _format_error_detail("delete_rule", e)
        logger.error(f"Error deleting rule: {error_detail}")
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )

