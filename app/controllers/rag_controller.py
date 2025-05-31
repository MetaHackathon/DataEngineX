import time
from fastapi import HTTPException
from typing import List

from app.models.rag_models import (
    PaperIndexRequest, PaperIndexResponse,
    SearchRequest, SearchResponse, SearchResult,
    AnnotationRequest, AnnotationResponse,
    SystemStatsResponse
)
from app.services.chunkr_service import ChunkrService

class RagController:
    """Controller for Personal Knowledge Base functionality"""
    
    def __init__(self):
        self.chunkr_service = ChunkrService()
    
    async def index_paper(self, paper_id: str, request: PaperIndexRequest) -> PaperIndexResponse:
        """Save a paper to personal knowledge base using AI processing"""
        start_time = time.time()
        
        try:
            # Process PDF with Chunkr AI
            chunks_data = await self.chunkr_service.process_pdf_from_url(str(request.pdf_url))
            
            # Prepare metadata
            metadata = {
                "title": request.title,
                "authors": request.authors,
                "year": request.year,
                "topics": request.topics or []
            }
            
            # Store processed chunks
            chunks_count = await self.chunkr_service.store_paper_chunks(
                paper_id, chunks_data, metadata
            )
            
            processing_time = time.time() - start_time
            
            return PaperIndexResponse(
                success=True,
                message=f"📚 Paper '{request.title}' saved to your knowledge base",
                paper_id=paper_id,
                chunks_count=chunks_count,
                processing_time=round(processing_time, 2)
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save paper to knowledge base: {str(e)}"
            )
    
    async def get_saved_papers(self):
        """Get list of papers in personal knowledge base"""
        try:
            return await self.chunkr_service.get_saved_papers()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get saved papers: {str(e)}"
            )
    
    async def search_paper(self, paper_id: str, request: SearchRequest) -> SearchResponse:
        """Search within a specific paper in your knowledge base"""
        try:
            chunks = await self.chunkr_service.search_paper_chunks(
                paper_id, request.query, request.limit
            )
            
            results = [
                SearchResult(
                    chunk_id=chunk["chunk_id"],
                    content=chunk["content"],
                    relevance_score=chunk["relevance_score"],
                    page_number=chunk.get("page_number"),
                    section=chunk.get("section")
                )
                for chunk in chunks
            ]
            
            return SearchResponse(
                query=request.query,
                paper_id=paper_id,
                results=results,
                total_results=len(results)
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {str(e)}"
            )
    
    async def index_annotation(self, paper_id: str, annotation_id: str, request: AnnotationRequest) -> AnnotationResponse:
        """Add annotation to a paper in your knowledge base"""
        try:
            await self.chunkr_service.store_annotation(
                annotation_id=annotation_id,
                paper_id=paper_id,
                content=request.content,
                highlight_text=request.highlight_text,
                user_id=request.user_id,
                page_number=request.page_number
            )
            
            return AnnotationResponse(
                success=True,
                message=f"📝 Annotation added to paper {paper_id}",
                annotation_id=annotation_id,
                paper_id=paper_id
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add annotation: {str(e)}"
            )
    
    async def delete_paper(self, paper_id: str):
        """Remove paper from knowledge base"""
        # For demo purposes, just return success
        return {
            "success": True,
            "message": f"🗑️ Paper {paper_id} removed from knowledge base",
            "paper_id": paper_id
        }
    
    async def get_system_stats(self) -> SystemStatsResponse:
        """Get knowledge base statistics"""
        try:
            stats = await self.chunkr_service.get_system_stats()
            
            return SystemStatsResponse(
                total_papers=stats["total_papers"],
                total_chunks=stats["total_chunks"],
                total_annotations=stats["total_annotations"],
                status=stats.get("status", "unknown"),
                message=stats.get("message", "Knowledge base ready")
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get system stats: {str(e)}"
            ) 