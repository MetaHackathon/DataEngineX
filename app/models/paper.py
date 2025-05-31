from pydantic import BaseModel, Field
from typing import Optional, List

class PaperResponse(BaseModel):
    id: str
    title: str
    abstract: Optional[str] = None
    authors: List[str]
    year: int
    citations: int = 0  # ArXiv doesn't provide citations, default to 0
    institution: Optional[str] = None
    impact: str = "low"  # We can determine this based on certain criteria
    url: str
    topics: List[str] = []

class ArxivQuery(BaseModel):
    search_query: str
    start: int = Field(default=0, ge=0)
    max_results: int = Field(default=10, ge=1, le=100)
    sort_by: str = Field(default="relevance", pattern="^(relevance|lastUpdatedDate|submittedDate)$")
    sort_order: str = Field(default="descending", pattern="^(ascending|descending)$") 