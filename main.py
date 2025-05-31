from fastapi import FastAPI, Query
from typing import List
import os
from dotenv import load_dotenv

from app.models.paper import PaperResponse
from app.models.rag_models import (
    PaperIndexRequest, PaperIndexResponse,
    SearchRequest, SearchResponse,
    AnnotationRequest, AnnotationResponse,
    SystemStatsResponse
)
from app.controllers.paper_controller import PaperController
from app.controllers.rag_controller import RagController

load_dotenv()

app = FastAPI(
    title="DataEngine",
    description="Research paper discovery and personal knowledge base builder",
    version="2.0.0"
)

# Initialize controllers
paper_controller = PaperController()
rag_controller = RagController()

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
async def save_paper_to_knowledge_base(paper_id: str, request: PaperIndexRequest):
    """
    Step 2: Save a selected paper to your personal knowledge base.
    This processes the paper with AI to enable intelligent search within its content.
    """
    return await rag_controller.index_paper(paper_id, request)

@app.get("/api/knowledge-base/papers")
async def get_saved_papers():
    """
    View all papers in your personal knowledge base.
    Shows what papers you've saved and can search within.
    """
    return await rag_controller.get_saved_papers()

@app.post("/api/knowledge-base/papers/{paper_id}/search", response_model=SearchResponse)
async def search_within_saved_paper(paper_id: str, request: SearchRequest):
    """
    Step 3: Search for specific content within a paper you've saved.
    This uses AI-powered chunking to find relevant sections quickly.
    """
    return await rag_controller.search_paper(paper_id, request)

@app.post("/api/knowledge-base/papers/{paper_id}/annotations/{annotation_id}", response_model=AnnotationResponse)
async def add_annotation_to_paper(paper_id: str, annotation_id: str, request: AnnotationRequest):
    """
    Step 4: Add personal notes and annotations to papers in your knowledge base.
    Your annotations become searchable along with the paper content.
    """
    return await rag_controller.index_annotation(paper_id, annotation_id, request)

@app.delete("/api/knowledge-base/papers/{paper_id}")
async def remove_paper_from_knowledge_base(paper_id: str):
    """Remove a paper from your personal knowledge base"""
    return await rag_controller.delete_paper(paper_id)

@app.get("/api/knowledge-base/stats", response_model=SystemStatsResponse)
async def get_knowledge_base_stats():
    """
    Get statistics about your personal knowledge base.
    Shows how many papers, chunks, and annotations you have.
    """
    return await rag_controller.get_system_stats()

# ===== DEMO WORKFLOW ENDPOINT =====

@app.post("/api/demo/complete-workflow")
async def demo_complete_workflow(
    query: str = Query(..., description="Search query for ArXiv"),
    paper_index: int = Query(0, ge=0, description="Which paper to save (0-based)"),
    search_query: str = Query(..., description="Search query within the saved paper")
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
        
        save_result = await rag_controller.index_paper(selected_paper.id, index_request)
        
        # Step 3: Search within the saved paper
        search_request = SearchRequest(query=search_query, limit=3)
        search_results = await rag_controller.search_paper(selected_paper.id, search_request)
        
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
