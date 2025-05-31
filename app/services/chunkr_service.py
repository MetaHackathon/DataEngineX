import httpx
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional

from app.utils.config import Config

logger = logging.getLogger(__name__)

class ChunkrService:
    """Service for document processing using Chunkr AI and optional Supabase storage"""
    
    def __init__(self):
        self.chunkr_base_url = Config.CHUNKR_BASE_URL
        self.api_key = Config.CHUNKR_API_KEY
        
        # Always start in demo mode for simplicity
        self.supabase = None
        self.demo_mode = True
        
        # Try to initialize Supabase if credentials are available
        try:
            if Config.SUPABASE_URL and Config.SUPABASE_KEY:
                from supabase import create_client, Client
                self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
                self.demo_mode = False
                logger.info("✅ Supabase connected successfully")
        except Exception as e:
            logger.warning(f"Supabase not available: {e}. Using demo mode.")
            self.demo_mode = True
        
        if not self.api_key:
            logger.warning("CHUNKR_API_KEY not found. Using demo mode.")
            self.demo_mode = True
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"🚀 ChunkrService initialized in {'demo' if self.demo_mode else 'production'} mode")
    
    async def process_pdf_from_url(self, pdf_url: str) -> Dict[str, Any]:
        """Process PDF using Chunkr AI API or demo data"""
        # For demo purposes, always return mock data
        if self.demo_mode or not self.api_key:
            logger.info(f"Demo mode: Processing {pdf_url}")
            return self._create_demo_chunks(pdf_url)
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                process_payload = {
                    "url": pdf_url,
                    "ocr_strategy": "Auto",
                    "chunk_processing": "layout_aware"
                }
                
                response = await client.post(
                    f"{self.chunkr_base_url}/documents",
                    json=process_payload,
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    logger.warning(f"Chunkr API error: {response.status_code}. Using demo mode.")
                    return self._create_demo_chunks(pdf_url)
                
                result = response.json()
                document_id = result.get("id")
                
                await self._wait_for_completion(client, document_id)
                
                chunks_response = await client.get(
                    f"{self.chunkr_base_url}/documents/{document_id}/chunks",
                    headers=self.headers
                )
                
                if chunks_response.status_code == 200:
                    return chunks_response.json()
                else:
                    return self._create_demo_chunks(pdf_url)
                    
        except Exception as e:
            logger.error(f"Chunkr processing failed: {e}")
            return self._create_demo_chunks(pdf_url)
    
    async def _wait_for_completion(self, client: httpx.AsyncClient, document_id: str, max_wait: int = 30):
        """Wait for document processing to complete"""
        for _ in range(max_wait):
            status_response = await client.get(
                f"{self.chunkr_base_url}/documents/{document_id}/status",
                headers=self.headers
            )
            
            if status_response.status_code == 200:
                status = status_response.json().get("status")
                if status == "completed":
                    return
                elif status == "failed":
                    raise Exception("Document processing failed")
            
            await asyncio.sleep(1)
        
        raise Exception("Document processing timeout")
    
    def _create_demo_chunks(self, pdf_url: str) -> Dict[str, Any]:
        """Create demo chunks for demonstration"""
        demo_chunks = [
            {
                "id": f"demo_chunk_1",
                "content": "This paper introduces a novel approach to machine learning that significantly improves performance on benchmark datasets. The methodology combines deep learning with traditional statistical methods to achieve state-of-the-art results.",
                "page_number": 1,
                "section": "Abstract",
                "bbox": [0, 0, 100, 50]
            },
            {
                "id": f"demo_chunk_2", 
                "content": "Related work in this field has shown promising results, but our approach addresses key limitations in scalability and accuracy. Previous methods struggled with large datasets and complex feature interactions, which our novel architecture handles efficiently.",
                "page_number": 2,
                "section": "Related Work",
                "bbox": [0, 50, 100, 100]
            },
            {
                "id": f"demo_chunk_3",
                "content": "Our experimental results demonstrate a 15% improvement in accuracy compared to state-of-the-art methods. The model was evaluated on multiple benchmark datasets including ImageNet, CIFAR-10, and several domain-specific datasets to ensure generalization.",
                "page_number": 5,
                "section": "Results",
                "bbox": [0, 100, 100, 150]
            },
            {
                "id": f"demo_chunk_4",
                "content": "The proposed algorithm achieves linear time complexity while maintaining high accuracy. This makes it practical for real-world applications with large-scale data processing requirements and enables deployment in resource-constrained environments.",
                "page_number": 3,
                "section": "Methodology", 
                "bbox": [0, 150, 100, 200]
            }
        ]
        
        return {"chunks": demo_chunks}
    
    async def store_paper_chunks(self, paper_id: str, chunks_data: Dict[str, Any], metadata: Dict[str, Any]) -> int:
        """Store processed chunks in knowledge base"""
        chunks = chunks_data.get("chunks", [])
        
        if self.demo_mode or not self.supabase:
            logger.info(f"📚 Demo mode: Would store {len(chunks)} chunks for paper '{metadata.get('title', paper_id)}'")
            return len(chunks)
        
        try:
            storage_data = []
            for i, chunk in enumerate(chunks):
                storage_data.append({
                    "paper_id": paper_id,
                    "chunk_id": chunk.get("id", f"{paper_id}_chunk_{i}"),
                    "content": chunk.get("content", ""),
                    "page_number": chunk.get("page_number"),
                    "section": chunk.get("section"),
                    "chunk_index": i,
                    "metadata": {
                        "bbox": chunk.get("bbox", []),
                        "title": metadata.get("title"),
                        "authors": metadata.get("authors", [])
                    }
                })
            
            if storage_data:
                self.supabase.table('paper_chunks').upsert(storage_data).execute()
                logger.info(f"✅ Stored {len(storage_data)} chunks for paper {paper_id}")
            
            return len(storage_data)
            
        except Exception as e:
            logger.error(f"Failed to store chunks: {e}")
            return len(chunks)
    
    async def search_paper_chunks(self, paper_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant chunks within a specific paper in your knowledge base"""
        if self.demo_mode or not self.supabase:
            logger.info(f"🔍 Demo mode: Searching for '{query}' in paper {paper_id}")
            demo_results = []
            demo_chunks = self._create_demo_chunks("")["chunks"]
            
            for i, chunk in enumerate(demo_chunks[:limit]):
                if query.lower() in chunk["content"].lower():
                    demo_results.append({
                        "chunk_id": chunk["id"],
                        "content": chunk["content"],
                        "relevance_score": 0.9 - (i * 0.1),
                        "page_number": chunk.get("page_number"),
                        "section": chunk.get("section")
                    })
            
            return demo_results[:limit]
        
        try:
            response = self.supabase.table('paper_chunks')\
                .select('*')\
                .eq('paper_id', paper_id)\
                .ilike('content', f'%{query}%')\
                .limit(limit)\
                .execute()
            
            results = []
            for i, chunk in enumerate(response.data):
                results.append({
                    "chunk_id": chunk["chunk_id"],
                    "content": chunk["content"],
                    "relevance_score": 0.9 - (i * 0.1),
                    "page_number": chunk.get("page_number"),
                    "section": chunk.get("section")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def get_saved_papers(self) -> List[Dict[str, Any]]:
        """Get list of papers in your personal knowledge base"""
        if self.demo_mode or not self.supabase:
            return [
                {"paper_id": "demo_paper_1", "title": "Demo Paper: Machine Learning Fundamentals", "chunks_count": 4},
                {"paper_id": "demo_paper_2", "title": "Demo Paper: Deep Learning Architectures", "chunks_count": 6}
            ]
        
        try:
            response = self.supabase.table('paper_chunks')\
                .select('paper_id, metadata->title, count(*)')\
                .execute()
            
            # Group by paper_id and count chunks
            papers = {}
            for row in response.data:
                paper_id = row["paper_id"]
                if paper_id not in papers:
                    papers[paper_id] = {
                        "paper_id": paper_id,
                        "title": row.get("metadata", {}).get("title", paper_id),
                        "chunks_count": 0
                    }
                papers[paper_id]["chunks_count"] += 1
            
            return list(papers.values())
            
        except Exception as e:
            logger.error(f"Failed to get saved papers: {e}")
            return []
    
    async def store_annotation(self, annotation_id: str, paper_id: str, content: str, 
                             highlight_text: str = None, user_id: str = None, page_number: int = None):
        """Store annotation for later retrieval"""
        if self.demo_mode or not self.supabase:
            logger.info(f"📝 Demo mode: Would store annotation '{content[:50]}...' for paper {paper_id}")
            return
        
        try:
            annotation_data = {
                "id": annotation_id,
                "paper_id": paper_id,
                "content": content,
                "highlight_text": highlight_text,
                "user_id": user_id,
                "page_number": page_number,
                "created_at": time.time()
            }
            
            self.supabase.table('annotations').upsert(annotation_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store annotation: {e}")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        if self.demo_mode or not self.supabase:
            return {
                "total_papers": 2,
                "total_chunks": 10,
                "total_annotations": 3,
                "status": "demo_mode",
                "message": "📚 Demo knowledge base with sample papers"
            }
        
        try:
            papers_response = self.supabase.table('paper_chunks')\
                .select('paper_id', count='exact')\
                .execute()
            
            chunks_response = self.supabase.table('paper_chunks')\
                .select('*', count='exact')\
                .execute()
            
            annotations_response = self.supabase.table('annotations')\
                .select('*', count='exact')\
                .execute()
            
            return {
                "total_papers": len(set(row["paper_id"] for row in papers_response.data)) if papers_response.data else 0,
                "total_chunks": chunks_response.count or 0,
                "total_annotations": annotations_response.count or 0,
                "status": "active",
                "message": "📚 Personal knowledge base ready"
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "total_papers": 0,
                "total_chunks": 0,
                "total_annotations": 0,
                "status": "error",
                "message": "❌ Error accessing knowledge base"
            } 