from fastapi import HTTPException, Query
from typing import List

from app.models.paper import PaperResponse
from app.services.arxiv_service import ArxivService

class PaperController:
    def __init__(self):
        self.arxiv_service = ArxivService()
    
    async def search_arxiv(
        self,
        query: str,
        start: int = 0,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending"
    ) -> List[PaperResponse]:
        """Search ArXiv for papers"""
        try:
            return await self.arxiv_service.search(
                query=query,
                start=start,
                max_results=max_results,
                sort_by=sort_by,
                sort_order=sort_order
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"ArXiv API error: {str(e)}"
            )
    
    async def get_recommended_papers(self, limit: int = 10) -> List[PaperResponse]:
        """Get recommended foundational papers"""
        try:
            return await self.arxiv_service.get_recommended_papers(limit)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching recommended papers: {str(e)}"
            )
    
    async def get_trending_papers(self, limit: int = 10) -> List[PaperResponse]:
        """Get trending papers from the last month"""
        try:
            return await self.arxiv_service.get_trending_papers(limit)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching trending papers: {str(e)}"
            ) 