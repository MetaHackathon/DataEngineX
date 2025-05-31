import os
from typing import Dict, Any

class Config:
    """Application configuration settings"""
    
    # API Settings
    ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
    API_TIMEOUT = 30.0
    
    # User Agent
    USER_AGENT = "DataEngine/1.0 (https://github.com/NeuxsAI/DataEngine)"
    
    # Rate Limiting
    RATE_LIMIT_DELAY = 1  # seconds to wait on 429 error
    
    # Impact Categories
    MAJOR_CATEGORIES = {'cs.AI', 'cs.LG', 'cs.CL', 'stat.ML'}
    RECENT_YEAR_THRESHOLD = 2020
    
    # Default Values
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_SORT_BY = "relevance"
    DEFAULT_SORT_ORDER = "descending"
    
    @classmethod
    def get_env_var(cls, key: str, default: Any = None) -> Any:
        """Get environment variable with optional default"""
        return os.getenv(key, default) 