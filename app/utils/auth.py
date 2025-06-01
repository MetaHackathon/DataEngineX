"""
Authentication utilities for DataEngineX
"""

from fastapi import HTTPException, Header
from typing import Optional
from uuid import UUID
import os
from ..utils.supabase_client import get_supabase
from ..models.research_models import UserContext

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> UUID:
    """Extract user ID from Supabase authorization header"""
    user_context = await get_current_user(authorization)
    return user_context.user_id

async def get_current_user(authorization: Optional[str] = Header(None)) -> UserContext:
    """Extract user context from Supabase authorization header"""
    if not authorization:
        # Demo mode - use demo user
        return UserContext(
            user_id=UUID("00000000-0000-0000-0000-000000000000"),
            email="demo@dataenginex.com",
            full_name="Demo User"
        )
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        
        # Validate token with Supabase
        supabase = get_supabase()
        user_response = supabase.auth.get_user(token)
        
        if user_response.user is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        user = user_response.user
        
        return UserContext(
            user_id=UUID(user.id),
            email=user.email or "",
            full_name=user.user_metadata.get("full_name") if user.user_metadata else None
        )
    except Exception as e:
        # For development/demo purposes, fallback to demo mode
        # In production, you might want to raise HTTPException(401, "Authentication required")
        return UserContext(
            user_id=UUID("00000000-0000-0000-0000-000000000000"),
            email="demo@dataenginex.com", 
            full_name="Demo User"
        ) 