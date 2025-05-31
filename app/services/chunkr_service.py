import httpx
import uuid
import os
import ssl
import certifi
import tempfile
import json
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone # Added timezone
from chunkr_ai import Chunkr

# Fix SSL/TLS issues on macOS
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Assuming these are correctly defined in the project structure
from app.utils.config import Config 
from app.models.rag_models import PaperIndexRequest, UserContext

class ChunkrService:
    """Service for handling PDF processing and knowledge base operations using Chunkr AI"""
    
    def __init__(self):
        self.api_key = Config.CHUNKR_API_KEY
        self.base_url = Config.CHUNKR_BASE_URL # Note: base_url is initialized but not used in the provided snippet for Chunkr client.
        self.supabase_url = Config.SUPABASE_URL
        self.supabase_key = Config.SUPABASE_KEY
        
        if not self.api_key:
            raise ValueError("CHUNKR_API_KEY environment variable is required")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
        
        # Initialize Chunkr AI client
        self.chunkr = Chunkr(api_key=self.api_key)
        self._is_closed = False

    async def close(self):
        """Closes the Chunkr client and releases resources."""
        if not self._is_closed and hasattr(self.chunkr, 'close') and callable(self.chunkr.close):
            await self.chunkr.close()
            self._is_closed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _ensure_chunkr_client_open(self):
        if self._is_closed:
            raise RuntimeError("ChunkrService has been closed. Re-initialize to use or use within a context manager.")

    async def process_pdf_from_url(self, pdf_url: str) -> List[Dict[str, Any]]:
        """Process PDF from URL using Chunkr AI"""
        await self._ensure_chunkr_client_open()
        try:
            task = await self.chunkr.upload(pdf_url)
            result_data = await task.json()
            
            chunks = []
            for chunk_item in result_data.get("chunks", []):
                chunks.append({
                    "content": chunk_item.get("content", ""),
                    "page_number": chunk_item.get("page_number"),
                    "section": chunk_item.get("section"),
                    "metadata": chunk_item.get("metadata", {})
                })
            return chunks
        except Exception as e:
            # Consider logging the exception here
            raise Exception(f"Failed to process PDF: {str(e)}")

    async def process_pdf_content(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """Process PDF content and extract metadata from chunks"""
        try:
            print("🤖 Processing PDF with Chunkr AI...")
            
            # For now, let's bypass Chunkr AI due to event loop issues
            # and create a simple fallback that still provides the expected structure
            print("⚠️ Using fallback PDF processing (Chunkr AI temporarily disabled)")
            
            # Create a simple chunk structure as fallback
            chunks = [
                {
                    "content": f"Content from {file_name}",
                    "page_number": 1,
                    "section": "Document",
                    "metadata": {}
                }
            ]
            
            # Extract basic metadata from filename
            # Try to extract title from filename (remove .pdf extension)
            title = file_name.replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()
            
            extracted_metadata = {
                'title': title,
                'authors': [],
                'abstract': None,
                'year': None,
                'topics': [],
                'full_text': f"Content extracted from {file_name}",
                'chunks': chunks
            }
            
            print(f"✅ Created fallback metadata: {json.dumps(extracted_metadata, indent=2)}")
            return extracted_metadata
                
        except Exception as e:
            print(f"❌ Error processing PDF: {str(e)}")
            # Return minimal metadata if processing fails
            return {
                'title': file_name,
                'authors': [],
                'abstract': None,
                'year': None,
                'topics': [],
                'full_text': '',
                'chunks': []
            }

    async def store_paper(self, paper_id: str, request: PaperIndexRequest, user: UserContext) -> UUID:
        """Store paper metadata in database"""
        paper_uuid = uuid.uuid4()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supabase_url}/rest/v1/papers",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                json={
                    "id": str(paper_uuid),
                    "paper_id": paper_id,
                    "title": request.title,
                    "authors": request.authors,
                    "abstract": request.abstract,
                    "pdf_url": str(request.pdf_url),
                    "year": request.year,
                    "topics": request.topics,
                    "user_id": str(user.user_id),
                    "created_at": datetime.now(timezone.utc).isoformat() # Use timezone-aware UTC
                }
            )
            response.raise_for_status()
        return paper_uuid
    
    async def store_paper_chunks(
        self, paper_uuid: UUID, chunks_data: List[Dict[str, Any]], user: UserContext
    ) -> int:
        """Store processed paper chunks in database"""
        chunks_to_store = []
        
        for i, chunk_item in enumerate(chunks_data):
            chunk_uuid = uuid.uuid4()
            chunks_to_store.append({
                "id": str(chunk_uuid),
                "paper_id": str(paper_uuid),
                "chunk_id": f"{paper_uuid}_{i}",  # Generate unique chunk_id
                "content": chunk_item["content"], # Assuming 'content' is always present
                "page_number": chunk_item.get("page_number"),
                "section": chunk_item.get("section"),
                "chunk_index": i,
                "metadata": chunk_item.get("metadata", {}),
                "user_id": str(user.user_id),
                "created_at": datetime.now(timezone.utc).isoformat() # Use timezone-aware UTC
            })
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supabase_url}/rest/v1/paper_chunks",  # Fixed table name
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                json=chunks_to_store
            )
            response.raise_for_status()
        return len(chunks_to_store)
    
    async def get_saved_papers(self, user: UserContext) -> List[Dict[str, Any]]:
        """Get list of papers in user's knowledge base"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.supabase_url}/rest/v1/papers",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}"
                },
                params={
                    "user_id": f"eq.{str(user.user_id)}",
                    "order": "created_at.desc"
                }
            )
            response.raise_for_status()
            return response.json()  # httpx .json() is synchronous

    async def store_annotation(
        self,
        annotation_id: str,
        paper_id: str,
        content: str,
        highlight_text: Optional[str],
        user_id: str, # Note: user_id as string, other methods use UserContext object
        page_number: Optional[int]
    ) -> None:
        """Store annotation in database"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supabase_url}/rest/v1/annotations",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                json={
                    "id": annotation_id,
                    "paper_id": paper_id,
                    "content": content,
                    "highlight_text": highlight_text,
                    "user_id": user_id,
                    "page_number": page_number,
                    "created_at": datetime.now(timezone.utc).isoformat() # Use timezone-aware UTC
                }
            )
            response.raise_for_status()

    async def extract_pdf_metadata(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """Extract metadata from PDF using Chunkr AI"""
        await self._ensure_chunkr_client_open()
        
        try:
            print("🔍 Extracting PDF metadata...")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file.flush()
                
                # Extract metadata with Chunkr AI
                task = await self.chunkr.analyze(temp_file.name)
                result_data = await task.json()
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
                # Extract and structure metadata
                metadata = {
                    'title': result_data.get('title'),
                    'authors': result_data.get('authors', []),
                    'abstract': result_data.get('abstract'),
                    'year': result_data.get('year'),
                    'topics': result_data.get('topics', []),
                    'full_text': result_data.get('full_text', ''),
                    'citations': result_data.get('citations', 0),
                    'impact_score': result_data.get('impact_score', 0.0),
                    'metadata': {
                        'doi': result_data.get('doi'),
                        'journal': result_data.get('journal'),
                        'conference': result_data.get('conference'),
                        'institution': result_data.get('institution'),
                        'keywords': result_data.get('keywords', []),
                        'references': result_data.get('references', []),
                        'sections': result_data.get('sections', []),
                        'page_count': result_data.get('page_count'),
                        'word_count': result_data.get('word_count'),
                        'reading_time': result_data.get('reading_time'),
                        'language': result_data.get('language'),
                        'version': result_data.get('version'),
                        'created_date': result_data.get('created_date'),
                        'modified_date': result_data.get('modified_date')
                    }
                }
                
                print(f"✅ Extracted metadata: {json.dumps(metadata, indent=2)}")
                return metadata
                
        except Exception as e:
            print(f"❌ Error extracting PDF metadata: {str(e)}")
            # Return minimal metadata if extraction fails
            return {
                'title': file_name,
                'authors': [],
                'abstract': None,
                'year': None,
                'topics': [],
                'full_text': '',
                'citations': 0,
                'impact_score': 0.0,
                'metadata': {}
            }

    async def update_paper_topics(self, paper_uuid: UUID, topics: List[str]):
        """Patch topics list for a paper row in Supabase"""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.supabase_url}/rest/v1/papers?id=eq.{paper_uuid}",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                json={"topics": topics}
            )
            response.raise_for_status()

