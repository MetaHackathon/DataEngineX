"""
Knowledge Canvas Controller
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from uuid import UUID
import json
import time
from datetime import datetime

from ..models.research_models import (
    KnowledgeCanvasRequest,
    KnowledgeCanvasResponse,
    DeepConnectionAnalysisRequest,
    DeepConnectionAnalysisResponse,
    ResearchInsightRequest,
    ResearchInsightResponse
)
from ..utils.supabase_client import get_supabase
from ..utils.auth import get_current_user_id
from ..services.llama_client import LlamaClient

router = APIRouter(prefix="/api/knowledge-canvas", tags=["Knowledge Canvas"])

# ============================================================================
# KNOWLEDGE CANVAS - DEEP RESEARCH CONNECTIONS
# ============================================================================

@router.post("/{kb_id}/generate", response_model=KnowledgeCanvasResponse)
async def generate_knowledge_canvas(
    kb_id: UUID,
    request: KnowledgeCanvasRequest,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    🧠 Generate Knowledge Canvas with Deep Research Connections
    
    This is the MAIN showcase of Llama 4's long context window:
    - Analyzes multiple full papers simultaneously
    - Discovers deep thematic connections
    - Maps methodology evolution across papers
    - Identifies research gaps and opportunities
    """
    try:
        start_time = time.time()
        supabase = get_supabase()
        llama_client = LlamaClient()
        
        # Verify knowledge base access
        kb_result = supabase.table('knowledge_bases').select('*').eq('id', str(kb_id)).eq('user_id', str(user_id)).execute()
        
        if not kb_result.data:
            raise HTTPException(status_code=404, detail="Knowledge base not found or access denied")
        
        kb_info = kb_result.data[0]
        
        # Get all papers from knowledge base with full content
        papers_result = supabase.rpc('get_knowledge_base_papers', {'p_kb_id': str(kb_id)}).execute()
        
        if not papers_result.data:
            raise HTTPException(status_code=400, detail="No papers in knowledge base to analyze")
        
        papers = papers_result.data
        
        # Get full paper content for long context analysis
        papers_with_content = await _get_papers_full_content(papers, supabase)
        
        # Generate knowledge canvas using long context
        canvas = await _generate_comprehensive_canvas(
            kb_info['name'],
            papers_with_content,
            request,
            llama_client
        )
        
        # Store canvas in database
        canvas_id = await _store_knowledge_canvas(canvas, kb_id, user_id, supabase)
        canvas.canvas_id = canvas_id
        
        # Log activity
        background_tasks.add_task(
            _log_canvas_activity,
            user_id,
            'knowledge_canvas_generate',
            kb_id,
            {'papers_analyzed': len(papers_with_content), 'processing_time': time.time() - start_time}
        )
        
        return canvas
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating knowledge canvas: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate knowledge canvas")

@router.post("/analyze-connections", response_model=DeepConnectionAnalysisResponse)
async def analyze_deep_connections(
    request: DeepConnectionAnalysisRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    🔗 Deep Connection Analysis Between Papers
    
    Uses Llama 4 long context to find:
    - Methodological relationships
    - Theoretical connections
    - Contradictory findings
    - Knowledge synthesis opportunities
    """
    try:
        supabase = get_supabase()
        llama_client = LlamaClient()
        
        # Get papers with full content
        papers_result = supabase.table('papers').select('*').in_('id', [str(pid) for pid in request.paper_ids]).eq('user_id', str(user_id)).execute()
        
        if not papers_result.data:
            raise HTTPException(status_code=404, detail="Papers not found or access denied")
        
        if len(papers_result.data) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 papers for connection analysis")
        
        # Perform deep connection analysis
        analysis = await _analyze_paper_connections(
            papers_result.data,
            request,
            llama_client
        )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error analyzing connections: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze connections")

@router.post("/research-insights", response_model=ResearchInsightResponse)
async def generate_research_insights(
    request: ResearchInsightRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    💡 Generate AI-Powered Research Insights
    
    Uses long context to analyze research context and generate:
    - Trending research topics
    - Emerging methodologies
    - Research opportunities
    - Collaboration suggestions
    """
    try:
        supabase = get_supabase()
        llama_client = LlamaClient()
        
        # Get context data based on type
        context_data = await _get_research_context_data(request, user_id, supabase)
        
        # Generate insights using long context
        insights = await _generate_research_insights(
            context_data,
            request,
            llama_client
        )
        
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating research insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate research insights")

@router.get("/{canvas_id}", response_model=KnowledgeCanvasResponse)
async def get_knowledge_canvas(
    canvas_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """Get a previously generated knowledge canvas"""
    try:
        supabase = get_supabase()
        
        canvas_result = supabase.table('knowledge_canvases').select('*').eq('id', str(canvas_id)).eq('user_id', str(user_id)).execute()
        
        if not canvas_result.data:
            raise HTTPException(status_code=404, detail="Knowledge canvas not found or access denied")
        
        canvas_data = canvas_result.data[0]
        
        return KnowledgeCanvasResponse(
            canvas_id=UUID(canvas_data['id']),
            title=canvas_data['title'],
            paper_network=canvas_data['paper_network'],
            research_themes=canvas_data['research_themes'],
            methodology_evolution=canvas_data['methodology_evolution'],
            research_timeline=canvas_data['research_timeline'],
            cross_paper_insights=canvas_data['cross_paper_insights'],
            research_gaps=canvas_data['research_gaps'],
            future_opportunities=canvas_data['future_opportunities'],
            collaboration_suggestions=canvas_data['collaboration_suggestions'],
            generated_at=canvas_data['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching knowledge canvas: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch knowledge canvas")

@router.get("/list/{kb_id}")
async def list_knowledge_canvases(
    kb_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """List all knowledge canvases for a knowledge base"""
    try:
        supabase = get_supabase()
        
        canvases_result = supabase.table('knowledge_canvases').select(
            'id, title, created_at, paper_count'
        ).eq('knowledge_base_id', str(kb_id)).eq('user_id', str(user_id)).order('created_at', desc=True).execute()
        
        return canvases_result.data or []
        
    except Exception as e:
        print(f"Error listing knowledge canvases: {e}")
        raise HTTPException(status_code=500, detail="Failed to list knowledge canvases")

# ============================================================================
# HELPER FUNCTIONS - THE REAL MAGIC HAPPENS HERE
# ============================================================================

async def _get_papers_full_content(papers: List[Dict[str, Any]], supabase) -> List[Dict[str, Any]]:
    """Get full content for papers to leverage long context window"""
    
    papers_with_content = []
    
    for paper in papers:
        # Get full text content
        paper_detail = supabase.table('papers').select('*').eq('id', paper['id']).execute()
        
        if paper_detail.data:
            full_paper = paper_detail.data[0]
            
            enhanced_paper = {
                "id": paper['id'],
                "title": paper['title'],
                "abstract": paper['abstract'],
                "authors": paper['authors'],
                "year": paper['year'],
                "topics": paper['topics'],
                "full_text": full_paper.get('full_text', '')[:30000],  # Limit per paper for context management
                "citations": paper.get('citations', 0),
                "venue": paper.get('venue', 'arXiv'),
                "qualityScore": paper.get('qualityScore', 80),
                "added_at": paper.get('added_at')
            }
            papers_with_content.append(enhanced_paper)
    
    return papers_with_content

async def _generate_comprehensive_canvas(
    kb_name: str,
    papers_with_content: List[Dict[str, Any]],
    request: KnowledgeCanvasRequest,
    llama_client: LlamaClient
) -> KnowledgeCanvasResponse:
    """
    Generate comprehensive knowledge canvas using Llama 4's long context
    This is the MAIN demonstration of long context capabilities
    """
    
    if not llama_client:
        # Fallback canvas
        return _generate_fallback_canvas(kb_name, papers_with_content)
    
    # Prepare the FULL context for Llama 4 (this is where we use the long context window!)
    full_context = _prepare_long_context(papers_with_content, request)
    
    prompt = f"""
    You are an expert research analyst creating a comprehensive knowledge canvas for the research collection: "{kb_name}"
    
    FULL RESEARCH CONTEXT:
    {full_context}
    
    Create a comprehensive knowledge canvas that reveals deep connections and insights.
    
    Generate a JSON response with the following structure:
    {{
      "title": "Knowledge Canvas: {kb_name}",
      "paper_network": {{
        "nodes": [
          {{"id": "paper_id", "title": "Paper Title", "centrality": 0.8, "themes": ["theme1", "theme2"], "year": 2023}},
          ...
        ],
        "edges": [
          {{"source": "paper1", "target": "paper2", "relationship": "builds_upon", "strength": 0.9, "explanation": "detailed explanation"}},
          ...
        ]
      }},
      "research_themes": [
        {{
          "theme": "Deep Learning Architectures",
          "papers": ["paper1", "paper2"],
          "evolution": "description of how this theme evolved",
          "key_insights": ["insight1", "insight2"],
          "maturity": "emerging/developing/mature"
        }},
        ...
      ],
      "methodology_evolution": {{
        "timeline": [
          {{"year": 2020, "methodologies": ["method1"], "breakthrough_papers": ["paper1"]}},
          ...
        ],
        "method_relationships": [
          {{"from": "method1", "to": "method2", "evolution_type": "refinement/replacement/combination"}}
        ]
      }},
      "research_timeline": [
        {{"year": 2020, "major_contributions": ["contribution1"], "papers": ["paper1"]}},
        ...
      ],
      "cross_paper_insights": [
        {{
          "insight": "Major insight across multiple papers",
          "supporting_papers": ["paper1", "paper2"],
          "evidence": "detailed evidence",
          "implications": "what this means for the field",
          "confidence": 0.9
        }},
        ...
      ],
      "research_gaps": [
        {{
          "gap": "Identified research gap",
          "evidence": "why this is a gap",
          "papers_highlighting": ["paper1"],
          "potential_impact": "high/medium/low",
          "suggested_approaches": ["approach1", "approach2"]
        }},
        ...
      ],
      "future_opportunities": [
        {{
          "opportunity": "Research opportunity",
          "rationale": "why this is promising",
          "required_expertise": ["skill1", "skill2"],
          "timeline": "near-term/medium-term/long-term",
          "potential_collaborators": ["field1", "field2"]
        }},
        ...
      ],
      "collaboration_suggestions": [
        {{
          "collaboration_type": "interdisciplinary/method-sharing/data-sharing",
          "papers_involved": ["paper1", "paper2"],
          "potential_outcome": "what could be achieved",
          "feasibility": 0.8
        }},
        ...
      ]
    }}
    
    Focus on:
    1. DEEP analysis leveraging the full content of all papers
    2. Non-obvious connections and insights
    3. Methodological relationships and evolution
    4. Research gaps that emerge from collective analysis
    5. Future opportunities based on current trends
    6. Actionable collaboration suggestions
    
    This analysis should demonstrate the power of long context by finding insights impossible with single-paper analysis.
    """
    
    try:
        response = await llama_client.generate_response(
            prompt,
            max_tokens=8000,  # Long response for comprehensive analysis
            temperature=0.3
        )
        
        canvas_data = json.loads(response)
        
        return KnowledgeCanvasResponse(
            canvas_id=UUID("00000000-0000-0000-0000-000000000000"),  # Will be set later
            title=canvas_data.get('title', f"Knowledge Canvas: {kb_name}"),
            paper_network=canvas_data.get('paper_network', {}),
            research_themes=canvas_data.get('research_themes', []),
            methodology_evolution=canvas_data.get('methodology_evolution', {}),
            research_timeline=canvas_data.get('research_timeline', []),
            cross_paper_insights=canvas_data.get('cross_paper_insights', []),
            research_gaps=canvas_data.get('research_gaps', []),
            future_opportunities=canvas_data.get('future_opportunities', []),
            collaboration_suggestions=canvas_data.get('collaboration_suggestions', [])
        )
        
    except Exception as e:
        print(f"Error in comprehensive canvas generation: {e}")
        return _generate_fallback_canvas(kb_name, papers_with_content)

def _prepare_long_context(papers_with_content: List[Dict[str, Any]], request: KnowledgeCanvasRequest) -> str:
    """
    Prepare the full long context for Llama 4
    This is where we leverage the 1M/10M context window!
    """
    
    context_parts = []
    
    context_parts.append("=== COMPLETE RESEARCH COLLECTION ANALYSIS ===\n")
    context_parts.append(f"Total Papers: {len(papers_with_content)}\n")
    
    # Include FULL paper content for deep analysis
    for i, paper in enumerate(papers_with_content):
        context_parts.append(f"\n--- PAPER {i+1}: {paper['title']} ({paper['year']}) ---")
        context_parts.append(f"Authors: {', '.join(paper['authors'])}")
        context_parts.append(f"Topics: {', '.join(paper['topics'])}")
        context_parts.append(f"Abstract: {paper['abstract']}")
        
        # Include substantial text content (this is the long context advantage!)
        if paper.get('full_text'):
            context_parts.append(f"Full Content (excerpt): {paper['full_text']}")
        
        context_parts.append(f"Quality Score: {paper.get('qualityScore', 'N/A')}")
        context_parts.append(f"Added: {paper.get('added_at', 'N/A')}")
        context_parts.append("")
    
    # Add analysis preferences
    if request.focus_areas:
        context_parts.append(f"\nFOCUS AREAS: {', '.join(request.focus_areas)}")
    
    context_parts.append(f"\nANALYSIS DEPTH: {request.analysis_depth}")
    context_parts.append(f"INCLUDE METHODOLOGY MAP: {request.include_methodology_map}")
    context_parts.append(f"INCLUDE TIMELINE: {request.include_timeline}")
    context_parts.append(f"INCLUDE RESEARCH GAPS: {request.include_research_gaps}")
    context_parts.append(f"INCLUDE FUTURE DIRECTIONS: {request.include_future_directions}")
    
    return "\n".join(context_parts)

async def _analyze_paper_connections(
    papers: List[Dict[str, Any]],
    request: DeepConnectionAnalysisRequest,
    llama_client: LlamaClient
) -> DeepConnectionAnalysisResponse:
    """Analyze deep connections between papers using long context"""
    
    if not llama_client:
        return _generate_fallback_connections(papers)
    
    # Prepare papers for analysis
    papers_content = []
    for paper in papers:
        content = {
            "id": paper['id'],
            "title": paper['title'],
            "abstract": paper.get('abstract', ''),
            "full_text": paper.get('full_text', '')[:20000],  # Substantial content per paper
            "authors": paper.get('authors', []),
            "year": paper.get('year'),
            "topics": paper.get('topics', [])
        }
        papers_content.append(content)
    
    prompt = f"""
    Analyze deep connections between these research papers:
    
    PAPERS FOR ANALYSIS:
    {json.dumps(papers_content, indent=2)}
    
    Analysis Types Requested: {request.analysis_types}
    Connection Depth: {request.connection_depth}
    Include Contradictions: {request.include_contradictions}
    Include Knowledge Gaps: {request.include_knowledge_gaps}
    
    Provide a comprehensive analysis in JSON format:
    {{
      "connections": [
        {{
          "paper1_id": "id1",
          "paper2_id": "id2",
          "connection_type": "methodology/theoretical/findings/citations",
          "strength": 0.9,
          "description": "detailed description of connection",
          "evidence": "specific evidence from papers",
          "implications": "what this connection means"
        }},
        ...
      ],
      "themes": [
        {{
          "theme": "Common Research Theme",
          "papers": ["id1", "id2"],
          "description": "theme description",
          "evolution": "how theme evolved across papers"
        }},
        ...
      ],
      "contradictions": [
        {{
          "paper1_id": "id1",
          "paper2_id": "id2",
          "contradiction_type": "findings/methodology/interpretation",
          "description": "description of contradiction",
          "potential_resolution": "possible ways to resolve",
          "significance": "why this matters"
        }},
        ...
      ],
      "knowledge_gaps": [
        {{
          "gap": "Identified gap",
          "evidence": "how papers reveal this gap",
          "papers_involved": ["id1", "id2"],
          "research_opportunity": "how to address this gap"
        }},
        ...
      ],
      "synthesis_opportunities": [
        {{
          "opportunity": "Synthesis opportunity",
          "papers_to_combine": ["id1", "id2"],
          "potential_outcome": "what could be achieved",
          "methodology": "how to synthesize"
        }},
        ...
      ],
      "collaboration_potential": [
        {{
          "type": "collaboration type",
          "papers": ["id1", "id2"],
          "rationale": "why collaborate",
          "expected_outcome": "what could be achieved"
        }},
        ...
      ],
      "confidence_scores": {{
        "overall": 0.85,
        "connections": 0.9,
        "contradictions": 0.8,
        "gaps": 0.75
      }}
    }}
    """
    
    try:
        response = await llama_client.generate_response(
            prompt,
            max_tokens=4000,
            temperature=0.3
        )
        
        analysis_data = json.loads(response)
        
        return DeepConnectionAnalysisResponse(
            connections=analysis_data.get('connections', []),
            themes=analysis_data.get('themes', []),
            contradictions=analysis_data.get('contradictions', []),
            knowledge_gaps=analysis_data.get('knowledge_gaps', []),
            synthesis_opportunities=analysis_data.get('synthesis_opportunities', []),
            collaboration_potential=analysis_data.get('collaboration_potential', []),
            confidence_scores=analysis_data.get('confidence_scores', {})
        )
        
    except Exception as e:
        print(f"Error in connection analysis: {e}")
        return _generate_fallback_connections(papers)

async def _generate_research_insights(
    context_data: Dict[str, Any],
    request: ResearchInsightRequest,
    llama_client: LlamaClient
) -> ResearchInsightResponse:
    """Generate AI-powered research insights using long context"""
    
    if not llama_client:
        return _generate_fallback_insights()
    
    prompt = f"""
    Generate comprehensive research insights based on this context:
    
    RESEARCH CONTEXT:
    {json.dumps(context_data, indent=2)}
    
    Insight Types Requested: {request.insight_types}
    Time Horizon: {request.time_horizon}
    Include Actionable Suggestions: {request.include_actionable_suggestions}
    
    Provide insights in JSON format:
    {{
      "insights": [
        {{
          "type": "trend/gap/opportunity/methodology",
          "title": "Insight Title",
          "description": "detailed description",
          "evidence": "supporting evidence",
          "confidence": 0.9,
          "impact": "high/medium/low"
        }},
        ...
      ],
      "trending_topics": [
        {{"topic": "Topic Name", "momentum": 0.8, "papers": ["id1", "id2"], "description": "why trending"}},
        ...
      ],
      "emerging_methodologies": [
        {{"methodology": "Method Name", "adoption_rate": 0.6, "advantages": ["adv1"], "papers": ["id1"]}},
        ...
      ],
      "research_opportunities": [
        {{
          "opportunity": "Research Opportunity",
          "rationale": "why this is promising",
          "required_resources": ["resource1"],
          "timeline": "timeline estimate",
          "potential_impact": "expected impact"
        }},
        ...
      ],
      "collaboration_suggestions": [
        {{
          "type": "collaboration type",
          "description": "collaboration description",
          "potential_partners": ["field1", "field2"],
          "expected_outcome": "outcome"
        }},
        ...
      ],
      "actionable_next_steps": [
        "specific action 1",
        "specific action 2"
      ],
      "confidence_assessment": {{
        "overall": 0.85,
        "trends": 0.9,
        "opportunities": 0.8
      }},
      "supporting_evidence": {{
        "trends": ["evidence1", "evidence2"],
        "opportunities": ["evidence3", "evidence4"]
      }}
    }}
    """
    
    try:
        response = await llama_client.generate_response(
            prompt,
            max_tokens=3000,
            temperature=0.4
        )
        
        insights_data = json.loads(response)
        
        return ResearchInsightResponse(
            insights=insights_data.get('insights', []),
            trending_topics=insights_data.get('trending_topics', []),
            emerging_methodologies=insights_data.get('emerging_methodologies', []),
            research_opportunities=insights_data.get('research_opportunities', []),
            collaboration_suggestions=insights_data.get('collaboration_suggestions', []),
            actionable_next_steps=insights_data.get('actionable_next_steps', []),
            confidence_assessment=insights_data.get('confidence_assessment', {}),
            supporting_evidence=insights_data.get('supporting_evidence', {})
        )
        
    except Exception as e:
        print(f"Error generating research insights: {e}")
        return _generate_fallback_insights()

# Fallback functions for when Llama is not available

def _generate_fallback_canvas(kb_name: str, papers: List[Dict[str, Any]]) -> KnowledgeCanvasResponse:
    """Generate a basic canvas when Llama is not available"""
    return KnowledgeCanvasResponse(
        canvas_id=UUID("00000000-0000-0000-0000-000000000000"),
        title=f"Knowledge Canvas: {kb_name}",
        paper_network={"nodes": [], "edges": []},
        research_themes=[],
        methodology_evolution={},
        research_timeline=[],
        cross_paper_insights=[],
        research_gaps=[],
        future_opportunities=[],
        collaboration_suggestions=[]
    )

def _generate_fallback_connections(papers: List[Dict[str, Any]]) -> DeepConnectionAnalysisResponse:
    """Generate basic connections when Llama is not available"""
    return DeepConnectionAnalysisResponse(
        connections=[],
        themes=[],
        contradictions=[],
        knowledge_gaps=[],
        synthesis_opportunities=[],
        collaboration_potential=[],
        confidence_scores={}
    )

def _generate_fallback_insights() -> ResearchInsightResponse:
    """Generate basic insights when Llama is not available"""
    return ResearchInsightResponse(
        insights=[],
        trending_topics=[],
        emerging_methodologies=[],
        research_opportunities=[],
        collaboration_suggestions=[],
        actionable_next_steps=[],
        confidence_assessment={},
        supporting_evidence={}
    )

# Database operations

async def _store_knowledge_canvas(canvas: KnowledgeCanvasResponse, kb_id: UUID, user_id: UUID, supabase) -> UUID:
    """Store knowledge canvas in database"""
    try:
        canvas_data = {
            "knowledge_base_id": str(kb_id),
            "user_id": str(user_id),
            "title": canvas.title,
            "paper_network": canvas.paper_network,
            "research_themes": canvas.research_themes,
            "methodology_evolution": canvas.methodology_evolution,
            "research_timeline": canvas.research_timeline,
            "cross_paper_insights": canvas.cross_paper_insights,
            "research_gaps": canvas.research_gaps,
            "future_opportunities": canvas.future_opportunities,
            "collaboration_suggestions": canvas.collaboration_suggestions,
            "paper_count": len(canvas.paper_network.get('nodes', []))
        }
        
        result = supabase.table('knowledge_canvases').insert(canvas_data).execute()
        
        if result.data:
            return UUID(result.data[0]['id'])
        else:
            return UUID("00000000-0000-0000-0000-000000000000")
            
    except Exception as e:
        print(f"Error storing canvas: {e}")
        return UUID("00000000-0000-0000-0000-000000000000")

async def _get_research_context_data(request: ResearchInsightRequest, user_id: UUID, supabase) -> Dict[str, Any]:
    """Get research context data for insights generation"""
    
    context_data = {}
    
    if request.context_type == "knowledge_base":
        # Get knowledge base papers
        papers_result = supabase.rpc('get_knowledge_base_papers', {'p_kb_id': str(request.context_id)}).execute()
        context_data["papers"] = papers_result.data or []
        
    elif request.context_type == "paper_collection":
        # Get specific paper collection
        papers_result = supabase.table('papers').select('*').eq('user_id', str(user_id)).execute()
        context_data["papers"] = papers_result.data or []
        
    # Add user context
    user_stats = supabase.rpc('get_enhanced_user_stats', {'p_user_id': str(user_id)}).execute()
    context_data["user_stats"] = user_stats.data or {}
    
    return context_data

async def _log_canvas_activity(user_id: UUID, activity_type: str, entity_id: UUID, metadata: dict = None):
    """Log canvas-related activity"""
    try:
        supabase = get_supabase()
        supabase.rpc('log_user_activity', {
            'p_user_id': str(user_id),
            'p_activity_type': activity_type,
            'p_entity_type': 'knowledge_canvas',
            'p_entity_id': str(entity_id),
            'p_metadata': json.dumps(metadata or {})
        }).execute()
    except Exception as e:
        print(f"Error logging canvas activity: {e}") 