"""
Supabase client utilities for DataEngineX
"""

import os
from supabase import create_client, Client
from typing import Optional

# Global client instance
_supabase_client: Optional[Client] = None

def get_supabase() -> Client:
    """Get the Supabase client instance"""
    global _supabase_client
    
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required")
        
        _supabase_client = create_client(supabase_url, supabase_key)
    
    return _supabase_client

def reset_supabase_client():
    """Reset the Supabase client (useful for testing)"""
    global _supabase_client
    _supabase_client = None 