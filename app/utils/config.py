import os
from typing import Dict, Any

class Config:
    """Application configuration settings"""
    
    # ArXiv API Settings
    ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
    API_TIMEOUT = 30.0
    USER_AGENT = "DataEngine/1.0 (https://github.com/NeuxsAI/DataEngine)"
    RATE_LIMIT_DELAY = 1  # seconds to wait on 429 error
    
    # Paper Categories and Impact
    MAJOR_CATEGORIES = {'cs.AI', 'cs.LG', 'cs.CL', 'stat.ML'}
    RECENT_YEAR_THRESHOLD = 2020
    
    # Search Defaults
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_SORT_BY = "relevance"
    DEFAULT_SORT_ORDER = "descending"
    
    # RAG Settings (Optional)
    CHUNKR_API_KEY = os.getenv("CHUNKR_API_KEY")
    CHUNKR_BASE_URL = "https://api.chunkr.ai/api/v1"
    
    # Storage Settings (Optional)
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # RAG Configuration
    DEFAULT_SEARCH_LIMIT = 5
    MAX_SEARCH_LIMIT = 20
    
    @classmethod
    def get_env_var(cls, key: str, default: Any = None) -> Any:
        """Get environment variable with optional default"""
        return os.getenv(key, default) 