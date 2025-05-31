from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional

class PaperIndexRequest(BaseModel):
    """Request model for indexing a paper"""
    paper_id: str
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    pdf_url: HttpUrl
    year: Optional[int] = None
    topics: Optional[List[str]] = None

class PaperIndexResponse(BaseModel):
    """Response model for paper indexing"""
    success: bool
    message: str
    paper_id: str
    chunks_count: Optional[int] = None
    processing_time: Optional[float] = None

class SearchRequest(BaseModel):
    """Request model for searching within a paper"""
    query: str
    limit: Optional[int] = Field(default=5, ge=1, le=20)

class SearchResult(BaseModel):
    """Individual search result"""
    chunk_id: str
    content: str
    relevance_score: float
    page_number: Optional[int] = None
    section: Optional[str] = None

class SearchResponse(BaseModel):
    """Response model for search results"""
    query: str
    paper_id: str
    results: List[SearchResult]
    total_results: int

class AnnotationRequest(BaseModel):
    """Request model for indexing annotations"""
    annotation_id: str
    content: str
    highlight_text: Optional[str] = None
    user_id: str
    page_number: Optional[int] = None

class AnnotationResponse(BaseModel):
    """Response model for annotation indexing"""
    success: bool
    message: str
    annotation_id: str
    paper_id: str

class SystemStatsResponse(BaseModel):
    """Response model for system statistics"""
    total_papers: int
    total_chunks: int
    total_annotations: int
    status: str
    message: str 