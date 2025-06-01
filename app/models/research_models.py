from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

# ============================================================================
# CORE USER & PAPER MODELS
# ============================================================================

class UserContext(BaseModel):
    """User context for authentication"""
    user_id: UUID
    email: Optional[str] = None
    full_name: Optional[str] = None

class PaperUploadRequest(BaseModel):
    """Request to upload a PDF paper"""
    file_name: str
    file_content: bytes
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    year: Optional[int] = None
    topics: Optional[List[str]] = None
    source: str = "upload"  # upload, arxiv, doi

class SavedPaper(BaseModel):
    """Paper in user's research library"""
    id: UUID
    paper_id: str
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    year: Optional[int] = None
    topics: List[str]
    pdf_url: str
    full_text: Optional[str] = None
    processing_status: str
    highlights_count: int = 0
    annotations_count: int = 0
    created_at: str
    updated_at: str

# ============================================================================
# ANNOTATIONS & HIGHLIGHTS
# ============================================================================

class CreateHighlightRequest(BaseModel):
    """Request to create a highlight in a paper"""
    paper_id: UUID
    text: str
    page_number: int
    position: Dict[str, Any]  # {start, end, rects: [{x, y, width, height}]}
    color: str = "yellow"

class HighlightResponse(BaseModel):
    """Highlight information"""
    id: UUID
    paper_id: UUID
    text: str
    page_number: int
    position: Dict[str, Any]
    color: str
    created_at: str

class CreateAnnotationRequest(BaseModel):
    """Request to create an annotation"""
    paper_id: UUID
    content: str
    highlight_id: Optional[UUID] = None
    annotation_type: str = "note"  # note, question, insight, critique
    page_number: Optional[int] = None
    position: Optional[Dict[str, Any]] = None
    tags: List[str] = []

class AnnotationResponse(BaseModel):
    """Annotation information"""
    id: UUID
    paper_id: UUID
    highlight_id: Optional[UUID] = None
    content: str
    annotation_type: str
    page_number: Optional[int] = None
    position: Optional[Dict[str, Any]] = None
    tags: List[str]
    created_at: str
    updated_at: str

# ============================================================================
# CHAT & ANALYSIS
# ============================================================================

class ChatSessionRequest(BaseModel):
    """Request to create a chat session"""
    paper_id: Optional[UUID] = None
    session_name: Optional[str] = None
    session_type: str = "paper"  # paper, collection, general

class ChatMessageRequest(BaseModel):
    """Request to send a chat message"""
    session_id: UUID
    message: str
    include_context: bool = True

class ChatMessageResponse(BaseModel):
    """Chat message response"""
    id: UUID
    session_id: UUID
    role: str  # user, assistant
    content: str
    sources: List[Dict[str, Any]] = []
    created_at: str

class ChatSessionResponse(BaseModel):
    """Chat session information"""
    id: UUID
    paper_id: Optional[UUID] = None
    session_name: str
    session_type: str
    messages_count: int
    created_at: str
    updated_at: str

# ============================================================================
# ANALYSIS & INSIGHTS
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request to analyze a paper"""
    paper_id: UUID
    analysis_type: str = "summary"  # summary, key_points, methodology, critique
    focus_areas: List[str] = []

class AnalysisResponse(BaseModel):
    """Analysis result"""
    id: UUID
    paper_id: UUID
    analysis_type: str
    content: str
    insights: List[str]
    key_quotes: List[Dict[str, Any]]
    related_concepts: List[str]
    created_at: str

class CompareRequest(BaseModel):
    """Request to compare papers"""
    paper_ids: List[UUID]
    comparison_type: str = "methodology"  # methodology, results, approaches

class ComparisonResponse(BaseModel):
    """Comparison result"""
    papers: List[SavedPaper]
    similarities: List[str]
    differences: List[str]
    synthesis: str
    recommendations: List[str]

# ============================================================================
# CONCEPTS & KNOWLEDGE GRAPH
# ============================================================================

class CreateConceptRequest(BaseModel):
    """Request to create a concept"""
    name: str
    description: Optional[str] = None
    concept_type: str = "user_defined"
    color: str = "#3B82F6"

class ConceptResponse(BaseModel):
    """Concept information"""
    id: UUID
    name: str
    description: Optional[str] = None
    concept_type: str
    color: str
    linked_papers: int
    linked_annotations: int
    created_at: str
    updated_at: str

class LinkConceptRequest(BaseModel):
    """Request to link a concept to content"""
    concept_id: UUID
    entity_type: str  # paper, annotation, highlight
    entity_id: UUID
    relevance_score: float = 1.0

# ============================================================================
# RESEARCH COLLECTIONS & WORKFLOWS
# ============================================================================

class CreateCollectionRequest(BaseModel):
    """Request to create a research collection"""
    name: str
    description: Optional[str] = None
    paper_ids: List[UUID] = []
    is_public: bool = False

class CollectionResponse(BaseModel):
    """Research collection information"""
    id: UUID
    name: str
    description: Optional[str] = None
    papers_count: int
    is_public: bool
    created_at: str
    updated_at: str

# ============================================================================
# SEARCH & DISCOVERY
# ============================================================================

class SearchRequest(BaseModel):
    """Request to search within user's library"""
    query: str
    search_in: List[str] = ["papers", "annotations", "highlights"]
    paper_ids: Optional[List[UUID]] = None
    limit: int = 20

class SearchResult(BaseModel):
    """Search result item"""
    id: UUID
    type: str  # paper, annotation, highlight
    title: str
    content: str
    paper_id: UUID
    paper_title: str
    relevance_score: float
    page_number: Optional[int] = None
    created_at: str

class SearchResponse(BaseModel):
    """Search results"""
    query: str
    total_results: int
    results: List[SearchResult]
    search_time: float

# ============================================================================
# SYSTEM RESPONSES
# ============================================================================

class PaperProcessResponse(BaseModel):
    """Response after processing a paper"""
    success: bool
    message: str
    paper: SavedPaper
    analysis_preview: Optional[str] = None
    processing_time: float

class LibraryStatsResponse(BaseModel):
    """User's research library statistics"""
    total_papers: int
    total_annotations: int
    total_highlights: int
    total_concepts: int
    total_collections: int
    recent_activity: List[Dict[str, Any]]
    storage_used_mb: float
    last_updated: str 