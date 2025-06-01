"""
Authentication utilities for DataEngineX
"""

from fastapi import HTTPException, Header
from typing import Optional
from uuid import UUID
import os
from ..utils.supabase_client import get_supabase
from ..models.research_models import UserContext

async def get_current_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-ID")) -> UUID:
    """Extract user ID from X-User-ID header (simplified approach)"""
    user_context = await get_current_user(x_user_id)
    return user_context.user_id

async def get_current_user(x_user_id: Optional[str] = Header(None, alias="X-User-ID")) -> UserContext:
    """Extract user context from X-User-ID header (simplified approach)"""
    if not x_user_id:
        # Demo mode - use demo user
        return UserContext(
            user_id=UUID("00000000-0000-0000-0000-000000000000"),
            email="demo@dataenginex.com",
            full_name="Demo User"
        )
    
    try:
        # Use the provided user ID directly
        return UserContext(
            user_id=UUID(x_user_id),
            email=f"user-{x_user_id}@delphix.com",
            full_name="DelphiX User"
        )
    except Exception as e:
        # For development/demo purposes, fallback to demo mode
        return UserContext(
            user_id=UUID("00000000-0000-0000-0000-000000000000"),
            email="demo@dataenginex.com", 
            full_name="Demo User"
        ) 