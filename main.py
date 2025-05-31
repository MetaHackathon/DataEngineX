from dotenv import load_dotenv
load_dotenv()  # Load environment variables FIRST

from fastapi import FastAPI, Query, Header, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
import os
from uuid import UUID
import jwt
import base64
import json

from app.models.paper import PaperResponse
from app.models.rag_models import (
    PaperIndexRequest, PaperIndexResponse,
    SearchRequest, SearchResponse,
    CreateAnnotationRequest, AnnotationResponse,
    SystemStatsResponse, SavedPaper, UserContext,
    PDFUploadRequest, PDFUploadResponse
)
from app.controllers.paper_controller import PaperController
from app.controllers.rag_controller import RagController

app = FastAPI(
    title="DataEngine",
    description="Research paper discovery and personal knowledge base builder",
    version="2.0.0"
)

# Initialize controllers
paper_controller = PaperController()
rag_controller = RagController()

# Authentication dependency
async def get_current_user(authorization: Optional[str] = Header(None)) -> UserContext:
    """Extract user context from Supabase JWT token"""
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
        
        # For now, decode without verification (Supabase handles verification)
        # In production, you'd verify with Supabase JWT secret
        payload = jwt.decode(token, options={"verify_signature": False})
        
        return UserContext(
            user_id=UUID(payload.get("sub")),
            email=payload.get("email"),
            full_name=payload.get("user_metadata", {}).get("full_name")
        )
    except Exception as e:
        # Fallback to demo mode if token parsing fails
        return UserContext(
            user_id=UUID("00000000-0000-0000-0000-000000000000"),
            email="demo@dataenginex.com", 
            full_name="Demo User"
        )

@app.get("/")
async def root():
    return {
        "message": "Welcome to DataEngine API - Paper Discovery + Personal Knowledge Base",
        "workflow": [
            "1. Search ArXiv for papers",
            "2. Select papers you want to save",
            "3. Add to your personal knowledge base",
            "4. Search within your saved papers"
        ],
        "docs": "/docs"
    }

# ===== PAPER DISCOVERY (Step 1) =====

@app.get("/api/arxiv/search", response_model=List[PaperResponse])
async def search_arxiv(
    query: str = Query(..., description="Search query (e.g., 'machine learning')"),
    start: int = Query(0, ge=0, description="Starting index"),
    max_results: int = Query(10, ge=1, le=100, description="Number of results to return"),
    sort_by: str = Query("relevance", pattern="^(relevance|lastUpdatedDate|submittedDate)$"),
    sort_order: str = Query("descending", pattern="^(ascending|descending)$")
):
    """Step 1: Search ArXiv for papers to discover relevant research"""
    return await paper_controller.search_arxiv(
        query=query,
        start=start,
        max_results=max_results,
        sort_by=sort_by,
        sort_order=sort_order
    )

@app.get("/api/papers/recommended", response_model=List[PaperResponse])
async def get_recommended_papers(
    limit: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """Discover foundational papers in computer science and machine learning"""
    return await paper_controller.get_recommended_papers(limit)

@app.get("/api/papers/trending", response_model=List[PaperResponse])
async def get_trending_papers(
    limit: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """Discover trending papers from the last month"""
    return await paper_controller.get_trending_papers(limit)

# ===== PERSONAL KNOWLEDGE BASE (Steps 2-4) =====

@app.post("/api/knowledge-base/papers/{paper_id}/save", response_model=PaperIndexResponse)
async def save_paper_to_knowledge_base(
    paper_id: str, 
    request: PaperIndexRequest, 
    user: UserContext = Depends(get_current_user)
):
    """
    Step 2: Save a selected paper to your personal knowledge base.
    This processes the paper with AI to enable intelligent search within its content.
    """
    return await rag_controller.index_paper(paper_id, request, user)

@app.get("/api/knowledge-base/papers", response_model=List[SavedPaper])
async def get_saved_papers(user: UserContext = Depends(get_current_user)):
    """
    Get all papers you've saved to your personal knowledge base.
    """
    return await rag_controller.get_saved_papers(user)

@app.post("/api/knowledge-base/papers/{paper_id}/annotations/{annotation_id}", response_model=AnnotationResponse)
async def add_annotation_to_paper(
    paper_id: str,
    annotation_id: str,
    request: CreateAnnotationRequest
):
    """Add an annotation to a paper in your knowledge base"""
    return await rag_controller.index_annotation(paper_id, annotation_id, request)

@app.delete("/api/knowledge-base/papers/{paper_id}")
async def remove_paper_from_knowledge_base(paper_id: str):
    """Remove a paper from your personal knowledge base"""
    return await rag_controller.delete_paper(paper_id)

# ===== KNOWLEDGE BASE CREATION =====

@app.post("/api/knowledge-base/upload", response_model=PaperResponse)
async def upload_paper_to_knowledge_base(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    authors: Optional[str] = Form(None),  # Comma-separated list
    abstract: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    topics: Optional[str] = Form(None),  # Comma-separated list
    metadata: Optional[str] = Form(None)  # JSON string
):
    """
    Upload a PDF paper to create a new knowledge base entry.
    The paper will be processed and stored in the user's personal knowledge base.
    """
    try:
        print(f"\n📄 Starting PDF upload process for file: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        print(f"📦 Read file content: {len(file_content)} bytes")
        
        # Parse optional fields
        authors_list = authors.split(",") if authors else None
        topics_list = topics.split(",") if topics else None
        metadata_dict = json.loads(metadata) if metadata else None
        
        print(f"📝 Parsed metadata:")
        print(f"  - Title: {title}")
        print(f"  - Authors: {authors_list}")
        print(f"  - Year: {year}")
        print(f"  - Topics: {topics_list}")
        
        # Create upload request
        upload_request = PDFUploadRequest(
            file_name=file.filename,
            file_content=file_content,
            title=title,
            authors=authors_list,
            abstract=abstract,
            year=year,
            topics=topics_list,
            metadata=metadata_dict
        )
        print("✅ Created upload request object")
        
        # Create demo user for testing
        demo_user = UserContext(
            user_id=UUID("00000000-0000-0000-0000-000000000000"),
            email="demo@dataenginex.com",
            full_name="Demo User"
        )
        print("👤 Using demo user for processing")
        
        # Process the upload
        print("🚀 Sending request to RAG controller for processing...")
        result = await rag_controller.process_pdf_upload(upload_request, demo_user)
        print("✨ Upload process completed successfully!")
        print(f"  - Paper Title: {result.title}")
        print(f"  - Paper ID: {result.id}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during upload process: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF upload: {str(e)}"
        )

# ===== DEMO WORKFLOW ENDPOINT =====

@app.post("/api/demo/complete-workflow")
async def demo_complete_workflow(
    query: str = Query(..., description="Search query for ArXiv"),
    paper_index: int = Query(0, ge=0, description="Which paper to save (0-based)"),
    search_query: str = Query(..., description="Search query within the saved paper"),
    user: UserContext = Depends(get_current_user)
):
    """
    🎯 Complete demo workflow for presentations:
    1. Search ArXiv for papers
    2. Save the selected paper to knowledge base  
    3. Search within the saved paper
    
    Perfect for demonstrating the full pipeline!
    """
    try:
        # Step 1: Search ArXiv
        papers = await paper_controller.search_arxiv(query=query, max_results=5)
        
        if not papers or paper_index >= len(papers):
            return {"error": "No papers found or invalid paper index"}
        
        selected_paper = papers[paper_index]
        
        # Step 2: Save paper to knowledge base
        index_request = PaperIndexRequest(
            paper_id=selected_paper.id,
            title=selected_paper.title,
            authors=selected_paper.authors,
            abstract=selected_paper.abstract,
            pdf_url=selected_paper.url,
            year=selected_paper.year,
            topics=selected_paper.topics
        )
        
        save_result = await rag_controller.index_paper(selected_paper.id, index_request, user)
        
        # Step 3: Search within the saved paper
        search_request = SearchRequest(query=search_query, limit=3)
        search_results = await rag_controller.search_paper(selected_paper.id, search_request, user)
        
        return {
            "workflow_success": True,
            "step_1_search_results": f"Found {len(papers)} papers matching '{query}'",
            "step_2_selected_paper": {
                "title": selected_paper.title,
                "id": selected_paper.id
            },
            "step_3_save_result": save_result,
            "step_4_search_results": search_results,
            "demo_message": "🎉 Complete workflow: Discovery → Save → Search → Results!"
        }
        
    except Exception as e:
        return {"error": f"Demo workflow failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
