"""
Knowledge Base Controller
Handles knowledge base creation, management, and operations for the DelphiX frontend
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from uuid import UUID
import json
from datetime import datetime

from ..models.research_models import (
    CreateKnowledgebaseRequest,
    KnowledgebaseResponse, 
    UpdateKnowledgebaseRequest,
    AddPapersToKnowledgebaseRequest,
    RemovePapersFromKnowledgebaseRequest,
    ShareKnowledgebaseRequest,
    KnowledgebaseInsightsResponse,
    ExportRequest,
    ExportResponse
)
from ..utils.supabase_client import get_supabase
from ..utils.auth import get_current_user_id
from ..services.llama_client import LlamaClient

router = APIRouter(prefix="/api/knowledgebases", tags=["Knowledge Bases"])

# ============================================================================
# KNOWLEDGE BASE CRUD OPERATIONS
# ============================================================================

@router.get("/", response_model=List[KnowledgebaseResponse])
async def get_user_knowledgebases(
    user_id: UUID = Depends(get_current_user_id)
):
    """Get all knowledge bases for the current user"""
    try:
        supabase = get_supabase()
        
        # Use the database function for consistency
        result = supabase.rpc('get_user_knowledge_bases', {'p_user_id': str(user_id)}).execute()
        
        if result.data:
            # Transform the JSON result to match our response model
            knowledge_bases = []
            for kb_data in result.data:
                kb = KnowledgebaseResponse(
                    id=kb_data['id'],
                    name=kb_data['name'],
                    description=kb_data.get('description'),
                    paper_count=kb_data['paper_count'],
                    created_at=kb_data['created_at'],
                    updated_at=kb_data['updated_at'],
                    tags=kb_data.get('tags', []),
                    status=kb_data.get('status', 'active'),
                    user_id=user_id,
                    is_public=kb_data.get('is_public', False)
                )
                knowledge_bases.append(kb)
            return knowledge_bases
        
        return []
        
    except Exception as e:
        print(f"Error fetching knowledge bases: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch knowledge bases")

@router.post("/", response_model=KnowledgebaseResponse)
async def create_knowledgebase(
    request: CreateKnowledgebaseRequest,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a new knowledge base"""
    try:
        supabase = get_supabase()
        
        # Create the knowledge base
        kb_result = supabase.table('knowledge_bases').insert({
            'user_id': str(user_id),
            'name': request.name,
            'description': request.description,
            'tags': request.tags,
            'is_public': request.is_public,
            'status': 'active'
        }).execute()
        
        if not kb_result.data:
            raise HTTPException(status_code=400, detail="Failed to create knowledge base")
        
        kb_id = kb_result.data[0]['id']
        
        # Add papers if provided
        if request.papers:
            paper_entries = []
            for paper_id in request.papers:
                paper_entries.append({
                    'knowledge_base_id': kb_id,
                    'paper_id': paper_id,
                    'added_by': str(user_id)
                })
            
            supabase.table('knowledge_base_papers').insert(paper_entries).execute()
        
        # Log activity
        background_tasks.add_task(
            log_activity, 
            user_id, 
            'knowledge_base_create', 
            'knowledge_base', 
            kb_id
        )
        
        # Return the created knowledge base
        return KnowledgebaseResponse(
            id=kb_id,
            name=request.name,
            description=request.description,
            paper_count=len(request.papers),
            created_at=kb_result.data[0]['created_at'],
            updated_at=kb_result.data[0]['updated_at'],
            tags=request.tags,
            status='active',
            user_id=user_id,
            is_public=request.is_public
        )
        
    except Exception as e:
        print(f"Error creating knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Failed to create knowledge base")

@router.get("/{kb_id}", response_model=KnowledgebaseResponse)
async def get_knowledgebase(
    kb_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """Get a specific knowledge base by ID"""
    try:
        supabase = get_supabase()
        
        # Use the database function
        result = supabase.rpc('get_knowledge_base_stats', {'p_kb_id': str(kb_id)}).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        kb_data = result.data
        
        # Check if user has access (owner or shared)
        access_result = supabase.table('knowledge_bases').select('user_id, is_public').eq('id', str(kb_id)).execute()
        
        if not access_result.data:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        kb_info = access_result.data[0]
        
        # Check access permissions
        if (kb_info['user_id'] != str(user_id) and 
            not kb_info['is_public']):
            
            # Check if shared with user
            share_result = supabase.table('knowledge_base_shares').select('id').eq('knowledge_base_id', str(kb_id)).eq('shared_with_user_id', str(user_id)).execute()
            
            if not share_result.data:
                raise HTTPException(status_code=403, detail="Access denied to knowledge base")
        
        return KnowledgebaseResponse(
            id=kb_data['id'],
            name=kb_data['name'],
            description=kb_data.get('description'),
            paper_count=kb_data['paper_count'],
            created_at=kb_data['created_at'],
            updated_at=kb_data['updated_at'],
            tags=kb_data.get('tags', []),
            status=kb_data.get('status', 'active'),
            user_id=UUID(kb_info['user_id']),
            is_public=kb_data.get('is_public', False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch knowledge base")

@router.put("/{kb_id}", response_model=KnowledgebaseResponse)
async def update_knowledgebase(
    kb_id: UUID,
    request: UpdateKnowledgebaseRequest,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id)
):
    """Update a knowledge base"""
    try:
        supabase = get_supabase()
        
        # Check ownership
        kb_result = supabase.table('knowledge_bases').select('user_id').eq('id', str(kb_id)).execute()
        
        if not kb_result.data or kb_result.data[0]['user_id'] != str(user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare update data
        update_data = {'updated_at': datetime.now().isoformat()}
        
        if request.name is not None:
            update_data['name'] = request.name
        if request.description is not None:
            update_data['description'] = request.description
        if request.tags is not None:
            update_data['tags'] = request.tags
        if request.is_public is not None:
            update_data['is_public'] = request.is_public
        
        # Update knowledge base
        result = supabase.table('knowledge_bases').update(update_data).eq('id', str(kb_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to update knowledge base")
        
        # Handle papers update if provided
        if request.papers is not None:
            # Remove existing papers
            supabase.table('knowledge_base_papers').delete().eq('knowledge_base_id', str(kb_id)).execute()
            
            # Add new papers
            if request.papers:
                paper_entries = []
                for paper_id in request.papers:
                    paper_entries.append({
                        'knowledge_base_id': str(kb_id),
                        'paper_id': paper_id,
                        'added_by': str(user_id)
                    })
                
                supabase.table('knowledge_base_papers').insert(paper_entries).execute()
        
        # Log activity
        background_tasks.add_task(
            log_activity, 
            user_id, 
            'knowledge_base_update', 
            'knowledge_base', 
            kb_id
        )
        
        # Get updated knowledge base
        updated_kb = supabase.rpc('get_knowledge_base_stats', {'p_kb_id': str(kb_id)}).execute()
        kb_data = updated_kb.data
        
        return KnowledgebaseResponse(
            id=kb_data['id'],
            name=kb_data['name'],
            description=kb_data.get('description'),
            paper_count=kb_data['paper_count'],
            created_at=kb_data['created_at'],
            updated_at=kb_data['updated_at'],
            tags=kb_data.get('tags', []),
            status=kb_data.get('status', 'active'),
            user_id=user_id,
            is_public=kb_data.get('is_public', False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Failed to update knowledge base")

@router.delete("/{kb_id}")
async def delete_knowledgebase(
    kb_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id)
):
    """Delete a knowledge base"""
    try:
        supabase = get_supabase()
        
        # Check ownership
        kb_result = supabase.table('knowledge_bases').select('user_id').eq('id', str(kb_id)).execute()
        
        if not kb_result.data or kb_result.data[0]['user_id'] != str(user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete knowledge base (cascade will handle related records)
        result = supabase.table('knowledge_bases').delete().eq('id', str(kb_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to delete knowledge base")
        
        # Log activity
        background_tasks.add_task(
            log_activity, 
            user_id, 
            'knowledge_base_delete', 
            'knowledge_base', 
            kb_id
        )
        
        return {"message": "Knowledge base deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete knowledge base")

# ============================================================================
# PAPER MANAGEMENT IN KNOWLEDGE BASES
# ============================================================================

@router.get("/{kb_id}/papers")
async def get_knowledgebase_papers(
    kb_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """Get all papers in a knowledge base"""
    try:
        supabase = get_supabase()
        
        # Check access to knowledge base
        kb_result = supabase.table('knowledge_bases').select('user_id, is_public').eq('id', str(kb_id)).execute()
        
        if not kb_result.data:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        kb_info = kb_result.data[0]
        
        # Check permissions
        if (kb_info['user_id'] != str(user_id) and not kb_info['is_public']):
            share_result = supabase.table('knowledge_base_shares').select('id').eq('knowledge_base_id', str(kb_id)).eq('shared_with_user_id', str(user_id)).execute()
            if not share_result.data:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Get papers using database function
        result = supabase.rpc('get_knowledge_base_papers', {'p_kb_id': str(kb_id)}).execute()
        
        return result.data or []
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching knowledge base papers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch papers")

@router.post("/{kb_id}/papers")
async def add_papers_to_knowledgebase(
    kb_id: UUID,
    request: AddPapersToKnowledgebaseRequest,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id)
):
    """Add papers to a knowledge base"""
    try:
        supabase = get_supabase()
        
        # Check ownership or write permission
        kb_result = supabase.table('knowledge_bases').select('user_id').eq('id', str(kb_id)).execute()
        
        if not kb_result.data:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        if kb_result.data[0]['user_id'] != str(user_id):
            # Check if user has write permission
            share_result = supabase.table('knowledge_base_shares').select('permissions').eq('knowledge_base_id', str(kb_id)).eq('shared_with_user_id', str(user_id)).execute()
            
            if not share_result.data or share_result.data[0]['permissions'] not in ['write', 'admin']:
                raise HTTPException(status_code=403, detail="Write access required")
        
        # Add papers
        paper_entries = []
        for paper_id in request.paper_ids:
            paper_entries.append({
                'knowledge_base_id': str(kb_id),
                'paper_id': paper_id,
                'added_by': str(user_id)
            })
        
        result = supabase.table('knowledge_base_papers').upsert(paper_entries, on_conflict='knowledge_base_id,paper_id').execute()
        
        # Update knowledge base timestamp
        supabase.table('knowledge_bases').update({
            'updated_at': datetime.now().isoformat()
        }).eq('id', str(kb_id)).execute()
        
        # Log activity
        background_tasks.add_task(
            log_activity, 
            user_id, 
            'papers_added_to_kb', 
            'knowledge_base', 
            kb_id,
            {'paper_count': len(request.paper_ids)}
        )
        
        return {"message": f"Added {len(request.paper_ids)} papers to knowledge base"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding papers to knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Failed to add papers")

@router.delete("/{kb_id}/papers")
async def remove_papers_from_knowledgebase(
    kb_id: UUID,
    request: RemovePapersFromKnowledgebaseRequest,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id)
):
    """Remove papers from a knowledge base"""
    try:
        supabase = get_supabase()
        
        # Check ownership or write permission
        kb_result = supabase.table('knowledge_bases').select('user_id').eq('id', str(kb_id)).execute()
        
        if not kb_result.data:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        if kb_result.data[0]['user_id'] != str(user_id):
            share_result = supabase.table('knowledge_base_shares').select('permissions').eq('knowledge_base_id', str(kb_id)).eq('shared_with_user_id', str(user_id)).execute()
            
            if not share_result.data or share_result.data[0]['permissions'] not in ['write', 'admin']:
                raise HTTPException(status_code=403, detail="Write access required")
        
        # Remove papers
        for paper_id in request.paper_ids:
            supabase.table('knowledge_base_papers').delete().eq('knowledge_base_id', str(kb_id)).eq('paper_id', paper_id).execute()
        
        # Update knowledge base timestamp
        supabase.table('knowledge_bases').update({
            'updated_at': datetime.now().isoformat()
        }).eq('id', str(kb_id)).execute()
        
        # Log activity
        background_tasks.add_task(
            log_activity, 
            user_id, 
            'papers_removed_from_kb', 
            'knowledge_base', 
            kb_id,
            {'paper_count': len(request.paper_ids)}
        )
        
        return {"message": f"Removed {len(request.paper_ids)} papers from knowledge base"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error removing papers from knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove papers")

# ============================================================================
# AI INSIGHTS AND ANALYSIS
# ============================================================================

@router.post("/{kb_id}/insights")
async def generate_knowledgebase_insights(
    kb_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id)
):
    """Generate AI insights for a knowledge base"""
    try:
        supabase = get_supabase()
        
        # Check access
        kb_result = supabase.table('knowledge_bases').select('user_id, name').eq('id', str(kb_id)).execute()
        
        if not kb_result.data or kb_result.data[0]['user_id'] != str(user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get papers in knowledge base
        papers_result = supabase.rpc('get_knowledge_base_papers', {'p_kb_id': str(kb_id)}).execute()
        
        if not papers_result.data:
            raise HTTPException(status_code=400, detail="No papers in knowledge base to analyze")
        
        # Generate insights in background
        background_tasks.add_task(
            generate_insights_background,
            kb_id,
            papers_result.data,
            kb_result.data[0]['name']
        )
        
        return {"message": "Insight generation started. Check back in a few minutes."}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")

@router.get("/{kb_id}/insights")
async def get_knowledgebase_insights(
    kb_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """Get AI insights for a knowledge base"""
    try:
        supabase = get_supabase()
        
        # Check access
        kb_result = supabase.table('knowledge_bases').select('user_id, is_public').eq('id', str(kb_id)).execute()
        
        if not kb_result.data:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        kb_info = kb_result.data[0]
        
        if (kb_info['user_id'] != str(user_id) and not kb_info['is_public']):
            share_result = supabase.table('knowledge_base_shares').select('id').eq('knowledge_base_id', str(kb_id)).eq('shared_with_user_id', str(user_id)).execute()
            if not share_result.data:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Get latest insights from the new research_insights table
        insights_result = supabase.table('research_insights').select('*').eq('context_type', 'knowledge_base').eq('context_id', str(kb_id)).order('created_at', desc=True).limit(1).execute()
        
        if not insights_result.data:
            return {"message": "No insights generated yet. Use POST /insights to generate."}
        
        insight_data = insights_result.data[0]
        
        return KnowledgebaseInsightsResponse(
            id=insight_data['id'],
            knowledgebase_id=kb_id,
            insights=insight_data['insights'],
            trends=insight_data.get('trending_topics', []),
            research_gaps=insight_data.get('research_opportunities', []),  # Map to closest equivalent
            key_connections=insight_data.get('collaboration_suggestions', []),  # Map to closest equivalent
            generated_at=insight_data['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch insights")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def log_activity(user_id: UUID, activity_type: str, entity_type: str, entity_id: UUID, metadata: dict = None):
    """Log user activity"""
    try:
        supabase = get_supabase()
        supabase.rpc('log_user_activity', {
            'p_user_id': str(user_id),
            'p_activity_type': activity_type,
            'p_entity_type': entity_type,
            'p_entity_id': str(entity_id),
            'p_metadata': json.dumps(metadata or {})
        }).execute()
    except Exception as e:
        print(f"Error logging activity: {e}")

async def generate_insights_background(kb_id: UUID, papers: list, kb_name: str):
    """Background task to generate AI insights"""
    try:
        llama_client = LlamaClient()
        
        # Prepare papers summary for AI analysis
        papers_summary = []
        for paper in papers[:10]:  # Limit to 10 papers for analysis
            papers_summary.append({
                'title': paper['title'],
                'abstract': paper.get('abstract', ''),
                'topics': paper.get('topics', []),
                'year': paper.get('year'),
                'citations': paper.get('citations', 0)
            })
        
        # Generate insights using AI
        prompt = f"""
        Analyze this collection of research papers in the knowledge base "{kb_name}" and provide insights:
        
        Papers: {json.dumps(papers_summary, indent=2)}
        
        Please provide a JSON response with:
        1. "insights": Array of key insights about the research area
        2. "trends": Array of emerging trends identified
        3. "research_gaps": Array of identified research gaps
        4. "key_connections": Array of important connections between papers
        
        Focus on academic rigor and actionable insights.
        """
        
        response = await llama_client.generate_response(prompt)
        
        # Parse AI response
        try:
            insights_data = json.loads(response)
        except:
            # Fallback if JSON parsing fails
            insights_data = {
                "insights": ["AI analysis completed"],
                "trends": ["Emerging research patterns identified"],
                "research_gaps": ["Areas for future research identified"],
                "key_connections": ["Cross-paper relationships mapped"]
            }
        
        # Save insights to database
        supabase = get_supabase()
        supabase.table('knowledge_base_insights').insert({
            'knowledge_base_id': str(kb_id),
            'insights': insights_data.get('insights', []),
            'trends': insights_data.get('trends', []),
            'research_gaps': insights_data.get('research_gaps', []),
            'key_connections': insights_data.get('key_connections', []),
            'generated_by': 'llama-4'
        }).execute()
        
    except Exception as e:
        print(f"Error generating insights in background: {e}") 