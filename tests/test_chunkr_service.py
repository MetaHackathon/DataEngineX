import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from dotenv import load_dotenv
load_dotenv() 

from app.services.chunkr_service import ChunkrService
from app.models.rag_models import PaperIndexRequest, UserContext

# Test data
TEST_PDF_URL = "https://arxiv.org/pdf/2303.08774.pdf"
TEST_USER = UserContext(user_id=uuid4(), email="test@example.com")
TEST_PAPER_REQUEST = PaperIndexRequest(
    paper_id="2303.08774",
    title="Test Paper",
    authors=["Test Author"],
    abstract="Test Abstract",
    pdf_url=TEST_PDF_URL,
    year=2023,
    topics=["AI", "ML"]
)

@pytest.fixture
def mock_chunkr():
    """Mock Chunkr AI SDK"""
    with patch('app.services.chunkr_service.Chunkr') as mock:
        # Mock upload method
        mock_task = AsyncMock()
        mock_task.json = AsyncMock(return_value={
            "chunks": [
                {
                    "content": "Test content",
                    "page_number": 1,
                    "section": "Introduction",
                    "metadata": {"key": "value"}
                }
            ]
        })
        mock.return_value.upload = AsyncMock(return_value=mock_task)
        
        # Mock search method
        mock.return_value.search = AsyncMock(return_value=[
            {
                "content": "Test search result",
                "score": 0.95,
                "page_number": 1,
                "section": "Results",
                "metadata": {"key": "value"}
            }
        ])
        
        # Mock close method
        mock.return_value.close = AsyncMock()
        
        yield mock

@pytest.fixture
def mock_httpx():
    """Mock HTTPX client for Supabase calls"""
    with patch('httpx.AsyncClient') as mock:
        mock_client = AsyncMock()
        
        # Mock successful responses for POST
        mock_post_response = AsyncMock()
        mock_post_response.raise_for_status = Mock()  # Non-async for sync call
        
        # Mock paper response for GET
        mock_paper_response = AsyncMock()
        mock_paper_response.raise_for_status = Mock()  # Non-async for sync call
        mock_paper_response.json = AsyncMock(return_value=[{
            "id": str(uuid4()),
            "title": TEST_PAPER_REQUEST.title,
            "authors": TEST_PAPER_REQUEST.authors,
            "created_at": datetime.utcnow().isoformat()
        }])
        
        # Mock count responses
        mock_papers_count = AsyncMock()
        mock_papers_count.raise_for_status = Mock()  # Non-async for sync call
        mock_papers_count.json = AsyncMock(return_value=[{"exact_count": 1}])
        
        mock_chunks_count = AsyncMock()
        mock_chunks_count.raise_for_status = Mock()  # Non-async for sync call
        mock_chunks_count.json = AsyncMock(return_value=[{"exact_count": 5}])
        
        mock_annotations_count = AsyncMock()
        mock_annotations_count.raise_for_status = Mock()  # Non-async for sync call
        mock_annotations_count.json = AsyncMock(return_value=[{"exact_count": 2}])
        
        # Set up client responses
        mock_client.post = AsyncMock(return_value=mock_post_response)
        
        # Set up different responses for different GET requests
        get_responses = {
            # Paper details
            lambda url, **kwargs: "/papers" in url and "count" not in url: mock_paper_response,
            # Count endpoints
            lambda url, **kwargs: "/papers/count" in url: mock_papers_count,
            lambda url, **kwargs: "/chunks/count" in url: mock_chunks_count,
            lambda url, **kwargs: "/annotations/count" in url: mock_annotations_count,
        }
        
        async def mock_get(url, **kwargs):
            for condition, response in get_responses.items():
                if condition(url, **kwargs):
                    return response
            return mock_paper_response  # Default response
        
        mock_client.get = AsyncMock(side_effect=mock_get)
        
        # Set up context manager
        mock.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock.return_value.__aexit__ = AsyncMock(return_value=None)
        
        yield mock

@pytest.fixture
def chunkr_service(mock_chunkr, mock_httpx):
    """Initialize ChunkrService with mocked dependencies"""
    with patch.object(ChunkrService, '__init__', return_value=None):
        service = ChunkrService()
        service.api_key = "test_api_key"
        service.supabase_url = "https://test.supabase.co"
        service.supabase_key = "test_supabase_key"
        service.chunkr = mock_chunkr.return_value
        service._is_closed = False  # Initialize the _is_closed attribute
        return service

@pytest.mark.asyncio
async def test_process_pdf_from_url(chunkr_service):
    """Test PDF processing functionality"""
    chunks = await chunkr_service.process_pdf_from_url(TEST_PDF_URL)
    
    assert chunks is not None
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    
    # Verify chunk structure
    chunk = chunks[0]
    assert "content" in chunk
    assert isinstance(chunk["content"], str)
    assert len(chunk["content"]) > 0
    assert "page_number" in chunk
    assert "section" in chunk
    assert "metadata" in chunk

@pytest.mark.asyncio
async def test_store_and_search_paper(chunkr_service):
    """Test paper storage and search functionality"""
    # Store paper
    paper_uuid = await chunkr_service.store_paper(
        paper_id=TEST_PAPER_REQUEST.paper_id,
        request=TEST_PAPER_REQUEST,
        user=TEST_USER
    )
    
    assert paper_uuid is not None
    
    # Process and store chunks
    chunks = await chunkr_service.process_pdf_from_url(TEST_PDF_URL)
    chunks_count = await chunkr_service.store_paper_chunks(
        paper_uuid=paper_uuid,
        chunks_data=chunks,
        user=TEST_USER
    )
    
    assert chunks_count > 0
    
    # Test search functionality
    search_results = await chunkr_service.search_paper_chunks(
        paper_id=TEST_PAPER_REQUEST.paper_id,
        query="machine learning",
        limit=5,
        user=TEST_USER
    )
    
    assert search_results is not None
    assert isinstance(search_results, list)
    assert len(search_results) > 0
    
    # Verify search result structure
    result = search_results[0]
    assert "content" in result
    assert "relevance_score" in result
    assert "paper_id" in result
    assert "paper_title" in result
    assert result["paper_title"] == TEST_PAPER_REQUEST.title

@pytest.mark.asyncio
async def test_annotation_functionality(chunkr_service):
    """Test annotation storage functionality"""
    annotation_id = str(uuid4())
    
    await chunkr_service.store_annotation(
        annotation_id=annotation_id,
        paper_id=TEST_PAPER_REQUEST.paper_id,
        content="Test annotation",
        highlight_text="highlighted text",
        user_id=str(TEST_USER.user_id),
        page_number=1
    )
    
    # Get system stats to verify annotation was stored
    stats = await chunkr_service.get_system_stats(TEST_USER)
    assert stats["total_annotations"] > 0

@pytest.mark.asyncio
async def test_get_saved_papers(chunkr_service):
    """Test retrieving saved papers"""
    papers = await chunkr_service.get_saved_papers(TEST_USER)
    
    assert papers is not None
    assert isinstance(papers, list)
    
    if len(papers) > 0:
        paper = papers[0]
        assert "id" in paper
        assert "title" in paper
        assert "authors" in paper
        assert "created_at" in paper

@pytest.mark.asyncio
async def test_get_system_stats(chunkr_service):
    """Test system statistics retrieval"""
    stats = await chunkr_service.get_system_stats(TEST_USER)
    
    assert stats is not None
    assert isinstance(stats, dict)
    assert "total_papers" in stats
    assert "total_chunks" in stats
    assert "total_annotations" in stats
    assert "status" in stats
    assert stats["status"] == "ready" 