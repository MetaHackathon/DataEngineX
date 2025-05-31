from fastapi import FastAPI, Query
from typing import List
import os
from dotenv import load_dotenv

from app.models.paper import PaperResponse
from app.controllers.paper_controller import PaperController

load_dotenv()

app = FastAPI(
    title="DataEngine",
    description="Microservice for gathering research paper metadata from multiple APIs",
    version="1.0.0"
)

# Initialize controllers
paper_controller = PaperController()

@app.get("/")
async def root():
    return {"message": "Welcome to DataEngine API"}

@app.get("/api/arxiv/search", response_model=List[PaperResponse])
async def search_arxiv(
    query: str = Query(..., description="Search query (e.g., 'machine learning')"),
    start: int = Query(0, ge=0, description="Starting index"),
    max_results: int = Query(10, ge=1, le=100, description="Number of results to return"),
    sort_by: str = Query("relevance", pattern="^(relevance|lastUpdatedDate|submittedDate)$"),
    sort_order: str = Query("descending", pattern="^(ascending|descending)$")
):
    """Search ArXiv for papers"""
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
    """Return foundational papers in computer science and machine learning"""
    return await paper_controller.get_recommended_papers(limit)

@app.get("/api/papers/trending", response_model=List[PaperResponse])
async def get_trending_papers(
    limit: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """Return trending papers from the last month in computer science and machine learning"""
    return await paper_controller.get_trending_papers(limit)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
