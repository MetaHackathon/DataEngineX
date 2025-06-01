"""
Papers Controller
Handles paper upload, processing, and management
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from typing import List, Optional
from uuid import UUID
import json
import httpx
from datetime import datetime

from ..models.research_models import PaperResponse, ScheduleDownloadRequest
from ..utils.supabase_client import get_supabase
from ..utils.auth import get_current_user_id
from ..services.llama_client import LlamaClient

router = APIRouter(prefix="/api/papers", tags=["Papers"])

# ... existing code ...

@router.post("/{paper_id}/schedule-download")
async def schedule_paper_download(
    paper_id: UUID,
    request: ScheduleDownloadRequest,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id)
):
    """Schedule background download of paper PDF"""
    try:
        supabase = get_supabase()
        
        # Check paper ownership
        paper_result = supabase.table('papers').select('user_id').eq('id', str(paper_id)).execute()
        if not paper_result.data or paper_result.data[0]['user_id'] != str(user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update paper with download URL and status
        supabase.table('papers').update({
            'pdf_url': request.url,
            'processing_status': 'pending_download',
            'updated_at': datetime.now().isoformat()
        }).eq('id', str(paper_id)).execute()
        
        # Schedule background download task
        background_tasks.add_task(
            download_paper_pdf,
            paper_id,
            request.url
        )
        
        return {"message": "PDF download scheduled"}
        
    except Exception as e:
        print(f"Error scheduling paper download: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule download")

async def download_paper_pdf(paper_id: UUID, url: str):
    """Background task to download paper PDF"""
    try:
        supabase = get_supabase()
        
        # Download PDF using httpx (supports following redirects)
        async with httpx.AsyncClient(follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; DelphiX/1.0; +https://delphix.ai)'
            }
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                # Get the PDF content as bytes
                pdf_content = response.content
                
                # Upload PDF to storage as a blob
                pdf_path = f"papers/{paper_id}/paper.pdf"
                
                # Upload the raw bytes directly
                supabase.storage.from_('papers').upload(
                    path=pdf_path,
                    file=pdf_content,
                    file_options={"contentType": "application/pdf"}
                )
                
                # Get public URL
                public_url = supabase.storage.from_('papers').get_public_url(pdf_path)
                
                # Update paper record with the public URL
                supabase.table('papers').update({
                    'pdf_url': public_url,
                    'processing_status': 'ready',
                    'updated_at': datetime.now().isoformat()
                }).eq('id', str(paper_id)).execute()
                
                print(f"Successfully downloaded and stored PDF for paper {paper_id}")
                
            else:
                raise Exception(f"Failed to download PDF: {response.status_code}")
                
    except Exception as e:
        print(f"Error downloading paper PDF: {e}")
        # Update paper status to failed
        supabase = get_supabase()
        supabase.table('papers').update({
            'processing_status': 'download_failed',
            'updated_at': datetime.now().isoformat()
        }).eq('id', str(paper_id)).execute() 