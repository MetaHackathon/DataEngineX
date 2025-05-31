import time
import os
import io
import json
import base64
from fastapi import HTTPException
from typing import List
import uuid

from llama_api_client import LlamaAPIClient

from app.models.rag_models import (
    PaperIndexRequest, PaperIndexResponse,
    SearchRequest, SearchResponse, SearchResult,
    CreateAnnotationRequest, AnnotationResponse,
    SystemStatsResponse, SavedPaper, UserContext,
    PDFUploadRequest, PDFUploadResponse, PaperDetail
)
from app.services.chunkr_service import ChunkrService
from app.models.paper import PaperResponse

class RagController:
    """Controller for Personal Knowledge Base functionality"""
    
    def __init__(self):
        self.chunkr_service = ChunkrService()
        # Initialize Llama API client
        self.llama_client = LlamaAPIClient(
            api_key=os.getenv("LLAMA_API_KEY"),
            base_url="https://api.llama.com/v1/",
        )
    
    async def process_pdf_upload(self, request: PDFUploadRequest, user: UserContext) -> PaperResponse:
        """Process uploaded PDF and create knowledge base entry"""
        start_time = time.time()
        
        try:
            print("\n🔄 Starting PDF processing in RAG controller")
            
            # Generate unique paper ID
            paper_id = str(uuid.uuid4())
            print(f"📌 Generated paper ID: {paper_id}")
            
            # Base64-encode PDF to send to Llama (truncated for token safety)
            pdf_b64 = base64.b64encode(request.file_content).decode()
            truncated_b64 = pdf_b64[:12000]  # keep prompt manageable

            # Ask Llama to extract metadata
            print("🤖 Asking Llama API to extract metadata...")
            prompt = (
                "You will receive a PDF encoded in base64. "
                "Return ONLY valid JSON with the following keys: "
                "title (string), authors (list of strings), abstract (string), "
                "year (integer or null), topics (list of strings).\n\n"
                "PDF (base64 truncated):\n" + truncated_b64
            )

            try:
                llama_response = self.llama_client.chat.completions.create(
                    model="Llama-4-Maverick-17B-128E-Instruct-FP8",
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                )
                # Support both possible response schemas
                if hasattr(llama_response, "completion_message"):
                    metadata_json_str = llama_response.completion_message.content.text.strip()
                elif hasattr(llama_response, "choices"):
                    metadata_json_str = llama_response.choices[0].message.content.strip()
                else:
                    metadata_json_str = str(llama_response)
                extracted = json.loads(metadata_json_str)
            except Exception as e:
                print(f"⚠️ Llama extraction failed: {str(e)}")
                extracted = {}

            # Use extracted metadata or fallback to user-provided / defaults
            title = request.title or extracted.get("title") or request.file_name.replace(".pdf", "")
            authors = request.authors or extracted.get("authors", [])
            abstract = request.abstract or extracted.get("abstract")
            year = request.year or extracted.get("year")
            topics = request.topics or extracted.get("topics", [])

            # Create placeholder chunk (content left empty to save space)
            chunk_data = [{
                "content": "",  # full text not stored in this flow
                "page_number": None,
                "section": "Document",
                "metadata": {}
            }]

            # Create paper detail
            paper_detail = PaperDetail(
                id=paper_id,
                paper_id=paper_id,  # Using UUID as paper_id for uploaded papers
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                topics=topics,
                pdf_url=f"uploaded://{paper_id}",  # Custom URL scheme for uploaded files
                full_text="",
                citations=0,
                impact_score=0.0,
                processing_status="completed",
                metadata=request.metadata or {},
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            )
            print("📄 Created paper detail object")
            
            # Store paper in database
            print("💾 Storing paper in database...")
            paper_uuid = await self.chunkr_service.store_paper(
                paper_id=paper_id,
                request=PaperIndexRequest(
                    paper_id=paper_id,
                    title=paper_detail.title,
                    authors=paper_detail.authors,
                    abstract=paper_detail.abstract,
                    pdf_url=paper_detail.pdf_url,
                    year=paper_detail.year,
                    topics=paper_detail.topics
                ),
                user=user
            )
            print(f"✅ Paper stored with UUID: {paper_uuid}")
            
            # Store processed chunks
            print("💾 Storing paper chunks...")
            chunks_count = await self.chunkr_service.store_paper_chunks(
                paper_uuid=paper_uuid,
                chunks_data=chunk_data,
                user=user
            )
            print(f"✅ Stored {chunks_count} chunks")
            
            # -------- SECOND LLAMA CALL: extract high-level topics --------
            print("📡 Requesting topics list from Llama…")
            topics_prompt = (
                "You will receive JSON metadata for a research paper and the PDF encoded in base64. "
                "Return ONLY a JSON array (list) of up to 8 high-level topics / keywords (strings, camelCase, no spaces).\n\n"
                f"Metadata:\n{json.dumps({'title': title, 'authors': authors, 'abstract': abstract, 'year': year}, ensure_ascii=False)}\n\n"
                "PDF (base64 truncated):\n" + truncated_b64
            )

            final_topics: List[str] = topics  # start with earlier list if any
            try:
                topics_resp = self.llama_client.chat.completions.create(
                    model="Llama-4-Maverick-17B-128E-Instruct-FP8",
                    messages=[{"role": "user", "content": topics_prompt}],
                )
                # Support both possible response schemas
                if hasattr(topics_resp, "completion_message"):
                    topics_text = topics_resp.completion_message.content.text.strip()
                elif hasattr(topics_resp, "choices"):
                    topics_text = topics_resp.choices[0].message.content.strip()
                else:
                    topics_text = str(topics_resp)
                topics_json = json.loads(topics_text)
                if isinstance(topics_json, list):
                    final_topics = topics_json[:8]
            except Exception as e:
                print(f"⚠️ Llama topics extraction failed: {str(e)}")

            # Update paper row with final topics list
            try:
                await self.chunkr_service.update_paper_topics(paper_uuid, final_topics)
                print("💾 Topics column updated in Supabase")
            except Exception as e:
                print(f"⚠️ Failed to update topics in Supabase: {str(e)}")

            processing_time = time.time() - start_time
            print(f"⏱️ Total processing time: {processing_time:.2f}s")
            
            # Build PaperResponse for frontend
            impact = (
                "high" if paper_detail.citations and paper_detail.citations > 100 else
                "medium" if paper_detail.citations and paper_detail.citations > 20 else
                "low"
            )
            return PaperResponse(
                id=str(paper_uuid),
                title=paper_detail.title,
                abstract=paper_detail.abstract,
                authors=paper_detail.authors,
                year=paper_detail.year or 0,
                citations=paper_detail.citations,
                institution=None,
                impact=impact,
                url=paper_detail.pdf_url,
                topics=final_topics,
            )
            
        except Exception as e:
            print(f"❌ Error in RAG controller: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process PDF upload: {str(e)}"
            )
    
    async def index_paper(self, paper_id: str, request: PaperIndexRequest, user: UserContext) -> PaperIndexResponse:
        """Save a paper to personal knowledge base using AI processing"""
        start_time = time.time()
        
        try:
            # Process PDF with Chunkr AI
            chunks_data = await self.chunkr_service.process_pdf_from_url(str(request.pdf_url))
            
            # Store complete paper first
            paper_uuid = await self.chunkr_service.store_paper(paper_id, request, user)
            
            # Store processed chunks
            chunks_count = await self.chunkr_service.store_paper_chunks(
                paper_uuid, chunks_data, user
            )
            
            processing_time = time.time() - start_time
            
            return PaperIndexResponse(
                success=True,
                message=f"📚 Paper '{request.title}' saved to your knowledge base",
                paper_id=paper_id,
                paper_uuid=paper_uuid,
                chunks_count=chunks_count,
                processing_time=round(processing_time, 2),
                processing_status="completed"
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save paper to knowledge base: {str(e)}"
            )
    
    async def get_saved_papers(self, user: UserContext):
        """Get list of papers in personal knowledge base"""
        try:
            return await self.chunkr_service.get_saved_papers(user)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get saved papers: {str(e)}"
            )
    
    async def index_annotation(self, paper_id: str, annotation_id: str, request: CreateAnnotationRequest) -> AnnotationResponse:
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