"""
Intelligent Search Controller
Handles AI-powered search with long context analysis
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import UUID

from ..models.research_models import (
    IntelligentSearchRequest,
    IntelligentSearchResponse,
    LiteratureReviewRequest,
    LiteratureReviewResponse
)
from ..services.intelligent_arxiv_service import IntelligentArxivService
from ..services.llama_client import LlamaClient
from ..utils.auth import get_current_user_id
from ..utils.supabase_client import get_supabase

router = APIRouter(prefix="/api/intelligent", tags=["Intelligent Search"])

# ============================================================================
# INTELLIGENT ARXIV SEARCH
# ============================================================================

@router.post("/search", response_model=IntelligentSearchResponse)
async def intelligent_arxiv_search(
    request: IntelligentSearchRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    🧠 Intelligent ArXiv search using Llama 4's long context
    
    Features:
    - Multiple query strategy generation
    - Context-aware paper discovery
    - AI-powered ranking and insights
    - Research gap identification
    """
    try:
        service = IntelligentArxivService()
        return await service.intelligent_search(request, user_id)
        
    except Exception as e:
        print(f"Error in intelligent search: {e}")
        raise HTTPException(status_code=500, detail="Intelligent search failed")

@router.post("/literature-review", response_model=LiteratureReviewResponse)
async def generate_literature_review(
    request: LiteratureReviewRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    📚 Generate comprehensive literature review using long context
    
    Analyzes up to 50 papers simultaneously to create:
    - Structured review sections
    - Methodology synthesis
    - Research gap analysis
    - Future directions
    """
    try:
        llama_client = LlamaClient()
        supabase = get_supabase()
        
        # Get papers for review
        papers = []
        if request.knowledge_base_id:
            kb_papers = supabase.rpc('get_knowledge_base_papers', {
                'p_kb_id': str(request.knowledge_base_id)
            }).execute()
            papers.extend(kb_papers.data or [])
        
        if request.paper_ids:
            for paper_id in request.paper_ids[:request.max_papers]:
                paper = supabase.table('papers').select('*').eq('id', str(paper_id)).execute()
                if paper.data:
                    papers.append(paper.data[0])
        
        if not papers:
            raise HTTPException(status_code=400, detail="No papers found for review")
        
        # Prepare long context with full paper content
        context_parts = [f"Literature Review Focus: {request.research_focus}\n"]
        
        for i, paper in enumerate(papers[:request.max_papers]):
            context_parts.append(f"""
Paper {i+1}:
Title: {paper.get('title')}
Authors: {', '.join(paper.get('authors', []))}
Year: {paper.get('year')}
Abstract: {paper.get('abstract', 'N/A')}
Full Text (first 5000 chars): {paper.get('full_text', 'N/A')[:5000]}
---
""")
        
        full_context = '\n'.join(context_parts)
        
        prompt = f"""
You are writing a comprehensive literature review on: "{request.research_focus}"

Based on the {len(papers)} papers provided, create a structured literature review with:

1. Title - A compelling title for the review
2. Abstract - 200-300 word summary
3. Sections - At least 5 main sections:
   - Introduction & Background
   - Methodology Overview
   - Key Findings & Contributions
   - Research Gaps & Limitations
   - Future Directions
4. Conclusions - 3-5 key takeaways
5. Methodology Synthesis - How methods evolved across papers
6. Paper Relationships - How papers connect and build on each other

Context with papers:
{full_context}

Return as JSON with the structure matching LiteratureReviewResponse.
Include proper citations using paper numbers [1], [2], etc.
"""
        
        response = await llama_client.generate_response(prompt)
        
        try:
            import json
            review_data = json.loads(response)
        except:
            # Fallback structure
            review_data = {
                "title": f"Literature Review: {request.research_focus}",
                "abstract": "This review synthesizes recent research...",
                "sections": [
                    {
                        "title": "Introduction",
                        "content": "Overview of the research area...",
                        "subsections": []
                    }
                ],
                "conclusions": ["Key finding 1", "Key finding 2"],
                "research_gaps": ["Gap 1", "Gap 2"],
                "methodology_synthesis": "Methods evolved from...",
                "future_directions": ["Direction 1", "Direction 2"],
                "paper_relationships": {},
                "citations": [f"[{i+1}] {p.get('title')}" for i, p in enumerate(papers)]
            }
        
        return LiteratureReviewResponse(**review_data)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating literature review: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate literature review")

@router.get("/search-history")
async def get_search_history(
    limit: int = 10,
    user_id: UUID = Depends(get_current_user_id)
):
    """Get user's intelligent search history"""
    try:
        supabase = get_supabase()
        
        result = supabase.table('intelligent_search_sessions').select('*').eq('user_id', str(user_id)).order('created_at', desc=True).limit(limit).execute()
        
        return result.data or []
        
    except Exception as e:
        print(f"Error getting search history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search history") 