from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

# ============================================================================
# CORE MODELS
# ============================================================================

class UserContext(BaseModel):
    """Internal model for user context (extracted from auth)"""
    user_id: UUID
    email: Optional[str] = None
    full_name: Optional[str] = None

# ============================================================================
# PAPER MANAGEMENT
# ============================================================================

class PaperIndexRequest(BaseModel):
    """Request to save a paper to knowledge base"""
    paper_id: str  # ArXiv ID, DOI, or custom
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    pdf_url: HttpUrl
    year: Optional[int] = None
    topics: Optional[List[str]] = None
    # user_id extracted from auth token

class PaperIndexResponse(BaseModel):
    """Response after indexing a paper"""
    success: bool
    message: str
    paper_id: str
    paper_uuid: UUID  # Internal UUID
    chunks_count: Optional[int] = None
    processing_time: Optional[float] = None
    processing_status: str

class SavedPaper(BaseModel):
    """Paper in user's knowledge base"""
    id: UUID
    paper_id: str
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    year: Optional[int] = None
    pdf_url: str
    chunks_count: int
    highlights_count: int
    annotations_count: int
    processing_status: str
    created_at: str
    updated_at: str

class PaperDetail(BaseModel):
    """Detailed paper information"""
    id: UUID
    paper_id: str
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    year: Optional[int] = None
    topics: List[str]
    pdf_url: str
    full_text: Optional[str] = None
    citations: int
    impact_score: float
    processing_status: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str

# ============================================================================
# SEARCH & CHUNKS
# ============================================================================

class SearchRequest(BaseModel):
    """Request to search within content"""
    query: str
    limit: Optional[int] = Field(default=5, ge=1, le=50)
    paper_id: Optional[UUID] = None  # Search within specific paper
    search_type: Optional[str] = Field(default="content", pattern="^(content|semantic|hybrid)$")

class SearchResult(BaseModel):
    """Individual search result"""
    id: UUID
    content: str
    relevance_score: float
    source_type: str  # chunk, annotation, highlight
    source_id: UUID
    paper_id: UUID
    paper_title: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    """Search results"""
    query: str
    total_results: int
    results: List[SearchResult]
    search_type: str
    search_time: float

# ============================================================================
# HIGHLIGHTS & ANNOTATIONS
# ============================================================================

class CreateHighlightRequest(BaseModel):
    """Request to create a highlight"""
    paper_id: UUID
    highlight_text: str
    page_number: int
    position: Dict[str, Any]  # {start, end, rects}
    color: Optional[str] = "yellow"

class HighlightResponse(BaseModel):
    """Highlight information"""
    id: UUID
    paper_id: UUID
    highlight_text: str
    page_number: int
    position: Dict[str, Any]
    color: str
    created_at: str

class CreateAnnotationRequest(BaseModel):
    """Request to create an annotation"""
    paper_id: UUID
    content: str
    highlight_id: Optional[UUID] = None
    annotation_type: Optional[str] = "note"
    page_number: Optional[int] = None
    position: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = []

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
# CONCEPTS & CONNECTIONS
# ============================================================================

class CreateConceptRequest(BaseModel):
    """Request to create a concept"""
    name: str
    description: Optional[str] = None
    concept_type: Optional[str] = "user_defined"
    color: Optional[str] = "#3B82F6"

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

class CreateConnectionRequest(BaseModel):
    """Request to create a connection"""
    source_type: str  # paper, concept, annotation
    source_id: UUID
    target_type: str  # paper, concept, annotation
    target_id: UUID
    connection_type: Optional[str] = "related"
    strength: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    description: Optional[str] = None

class ConnectionResponse(BaseModel):
    """Connection information"""
    id: UUID
    source_type: str
    source_id: UUID
    target_type: str
    target_id: UUID
    connection_type: str
    strength: float
    description: Optional[str] = None
    created_at: str

# ============================================================================
# KNOWLEDGE CANVAS
# ============================================================================

class CreateCanvasRequest(BaseModel):
    """Request to create a canvas"""
    name: str
    description: Optional[str] = None
    is_public: Optional[bool] = False

class CanvasResponse(BaseModel):
    """Canvas information"""
    id: UUID
    name: str
    description: Optional[str] = None
    canvas_data: Dict[str, Any]
    items_count: int
    is_public: bool
    created_at: str
    updated_at: str

class CreateCanvasItemRequest(BaseModel):
    """Request to create a canvas item"""
    canvas_id: UUID
    item_type: str  # paper, concept, annotation, note, group
    entity_id: Optional[UUID] = None
    position: Dict[str, Any]  # {x, y, z}
    size: Optional[Dict[str, Any]] = {"width": 200, "height": 100}
    style: Optional[Dict[str, Any]] = {}
    data: Optional[Dict[str, Any]] = {}

class CanvasItemResponse(BaseModel):
    """Canvas item information"""
    id: UUID
    canvas_id: UUID
    item_type: str
    entity_id: Optional[UUID] = None
    position: Dict[str, Any]
    size: Dict[str, Any]
    style: Dict[str, Any]
    data: Dict[str, Any]
    created_at: str
    updated_at: str

# ============================================================================
# CHAT & CONVERSATIONS
# ============================================================================

class CreateChatSessionRequest(BaseModel):
    """Request to create a chat session"""
    paper_id: Optional[UUID] = None
    session_name: Optional[str] = None
    session_type: Optional[str] = "document"
    context: Optional[Dict[str, Any]] = {}

class ChatSessionResponse(BaseModel):
    """Chat session information"""
    id: UUID
    paper_id: Optional[UUID] = None
    session_name: Optional[str] = None
    session_type: str
    messages_count: int
    context: Dict[str, Any]
    created_at: str
    updated_at: str

class SendChatMessageRequest(BaseModel):
    """Request to send a chat message"""
    session_id: UUID
    content: str
    message_type: Optional[str] = "text"

class ChatMessageResponse(BaseModel):
    """Chat message information"""
    id: UUID
    session_id: UUID
    role: str  # user, assistant, system
    content: str
    message_type: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: str

# ============================================================================
# RESEARCH CHAINS
# ============================================================================

class CreateResearchChainRequest(BaseModel):
    """Request to create a research chain"""
    name: str
    description: Optional[str] = None
    chain_type: Optional[str] = "research"

class ResearchChainResponse(BaseModel):
    """Research chain information"""
    id: UUID
    name: str
    description: Optional[str] = None
    chain_type: str
    status: str
    events_count: int
    created_at: str
    updated_at: str

class ResearchEventResponse(BaseModel):
    """Research event information"""
    id: UUID
    chain_id: UUID
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    description: Optional[str] = None
    sequence_order: int
    event_data: Dict[str, Any]
    created_at: str

# ============================================================================
# SYSTEM & STATISTICS
# ============================================================================

class SystemStatsResponse(BaseModel):
    """Comprehensive user statistics"""
    total_papers: int
    completed_papers: int
    total_chunks: int
    total_highlights: int
    total_annotations: int
    total_concepts: int
    total_connections: int
    total_canvases: int
    total_chat_sessions: int
    total_research_chains: int
    processing_papers: int
    status: str
    message: str

class UniversalSearchResponse(BaseModel):
    """Universal search across all user content"""
    query: str
    papers: List[Dict[str, Any]]
    chunks: List[Dict[str, Any]]
    annotations: List[Dict[str, Any]]
    concepts: List[Dict[str, Any]]
    total_results: int

# ============================================================================
# LEGACY COMPATIBILITY (for existing endpoints)
# ============================================================================

class PaperIndexRequest_Legacy(BaseModel):
    """Legacy model for backward compatibility"""
    paper_id: str
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    pdf_url: HttpUrl
    year: Optional[int] = None
    topics: Optional[List[str]] = None

class AnnotationRequest_Legacy(BaseModel):
    """Legacy annotation model"""
    annotation_id: str
    content: str
    highlight_text: Optional[str] = None
    user_id: str
    page_number: Optional[int] = None 