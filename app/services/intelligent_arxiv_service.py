"""
Intelligent ArXiv Service
Leverages Llama 4's long context capabilities for enhanced paper discovery
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio
from datetime import datetime
import json

from .arxiv_service import ArxivService
from .llama_client import LlamaClient
from ..utils.supabase_client import get_supabase
from ..models.research_models import (
    IntelligentSearchRequest,
    IntelligentSearchResponse,
    ResearchContext
)


class IntelligentArxivService:
    """Enhanced ArXiv service using Llama 4's long context for intelligent paper discovery"""
    
    def __init__(self):
        self.arxiv_service = ArxivService()
        self.llama_client = LlamaClient()
        self.supabase = get_supabase()
    
    async def intelligent_search(
        self,
        request: IntelligentSearchRequest,
        user_id: UUID
    ) -> IntelligentSearchResponse:
        """
        Perform intelligent ArXiv search using multiple query strategies
        and Llama 4's long context for ranking
        """
        start_time = datetime.now()
        
        # Build research context
        research_context = await self._build_research_context(request, user_id)
        
        # Generate multiple query strategies using Llama 4
        query_strategies = await self._generate_query_strategies(
            request.research_question,
            research_context
        )
        
        # Execute searches with all strategies in parallel
        all_papers = await self._execute_multi_strategy_search(query_strategies, request)
        
        # Use Llama 4's long context to analyze and rank papers
        ranked_papers, insights = await self._analyze_and_rank_papers(
            all_papers,
            request,
            research_context
        )
        
        # Save search session
        await self._save_search_session(
            user_id,
            request,
            query_strategies,
            all_papers,
            ranked_papers,
            insights
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return IntelligentSearchResponse(
            papers=ranked_papers[:request.max_papers],
            total_candidates=len(all_papers),
            query_strategies=query_strategies,
            research_insights=insights,
            processing_time=processing_time,
            confidence_score=insights.get('confidence_score', 0.8),
            suggested_refinements=insights.get('suggested_refinements', []),
            related_research_areas=insights.get('related_areas', [])
        )
    
    async def _build_research_context(
        self,
        request: IntelligentSearchRequest,
        user_id: UUID
    ) -> ResearchContext:
        """Build comprehensive research context from user's history"""
        context_data = {
            'research_question': request.research_question,
            'user_papers': [],
            'knowledge_base_papers': [],
            'research_areas': [],
            'methodologies': request.methodology_focus.split(',') if request.methodology_focus else [],
            'recent_searches': []
        }
        
        # Get user's recent papers
        papers_result = self.supabase.table('papers').select('*').eq('user_id', str(user_id)).order('created_at', desc=True).limit(10).execute()
        if papers_result.data:
            context_data['user_papers'] = papers_result.data
        
        # Get knowledge base papers if specified
        if request.knowledge_base_id:
            kb_papers = self.supabase.rpc('get_knowledge_base_papers', {'p_kb_id': str(request.knowledge_base_id)}).execute()
            if kb_papers.data:
                context_data['knowledge_base_papers'] = kb_papers.data
        
        # Get recent searches
        searches = self.supabase.table('search_history').select('*').eq('user_id', str(user_id)).order('created_at', desc=True).limit(5).execute()
        if searches.data:
            context_data['recent_searches'] = searches.data
        
        return ResearchContext(**context_data)
    
    async def _generate_query_strategies(
        self,
        research_question: str,
        context: ResearchContext
    ) -> List[Dict[str, Any]]:
        """Use Llama 4 to generate multiple query strategies"""
        
        prompt = f"""
        Generate multiple ArXiv search strategies for this research question:
        "{research_question}"
        
        User Context:
        - Has {len(context.user_papers)} papers in library
        - Research areas: {', '.join(context.research_areas[:5])}
        - Methodologies of interest: {', '.join(context.methodologies)}
        
        Generate 3-5 different search query strategies. Return as JSON array with:
        - query: The actual search query string
        - strategy_type: "broad", "specific", "methodological", "foundational", or "recent"
        - reasoning: Why this query strategy
        
        Be creative and comprehensive to maximize paper discovery.
        """
        
        try:
            response = await self.llama_client.generate_response(prompt)
            strategies = json.loads(response)
            return strategies
        except:
            # Diverse fallback strategies to maximize discovery
            keywords = research_question.split()
            
            strategies = [
                {
                    "query": research_question,
                    "strategy_type": "direct",
                    "reasoning": "Direct search with user's exact question"
                }
            ]
            
            # Add more diverse strategies based on keywords
            if len(keywords) >= 2:
                # Strategy 2: Individual key terms
                strategies.append({
                    "query": f"({keywords[0]}) AND ({keywords[-1]})",
                    "strategy_type": "methodological", 
                    "reasoning": "Focus on core methodology and application"
                })
                
                # Strategy 3: Broader category search
                strategies.append({
                    "query": f"cat:cs.CV OR cat:cs.LG OR cat:cs.AI {keywords[0]}",
                    "strategy_type": "broad",
                    "reasoning": "Search in relevant ArXiv categories"
                })
                
                # Strategy 4: Alternative terms
                alt_terms = {
                    "deep learning": "neural networks",
                    "computer vision": "image processing", 
                    "machine learning": "artificial intelligence",
                    "neural networks": "deep learning",
                    "transformers": "attention mechanisms"
                }
                
                alt_query = research_question
                for original, alternative in alt_terms.items():
                    if original in research_question.lower():
                        alt_query = research_question.lower().replace(original, alternative)
                        break
                
                strategies.append({
                    "query": alt_query,
                    "strategy_type": "alternative",
                    "reasoning": "Search with alternative terminology"
                })
            else:
                # Fallback for single keywords
                strategies.extend([
                    {
                        "query": f"cat:cs.AI {research_question}",
                        "strategy_type": "broad",
                        "reasoning": "Search in AI category"
                    },
                    {
                        "query": f"{research_question} applications",
                        "strategy_type": "applied",
                        "reasoning": "Find practical applications"
                    }
                ])
            
            return strategies
    
    async def _execute_multi_strategy_search(
        self,
        strategies: List[Dict[str, Any]],
        request: IntelligentSearchRequest
    ) -> List[Dict[str, Any]]:
        """Execute searches for all strategies in parallel"""
        
        async def search_with_strategy(strategy):
            try:
                # Add filters based on request
                filters = {}
                if request.time_range_years:
                    filters['year_range'] = f"last_{request.time_range_years}_years"
                
                papers = await self.arxiv_service.search(
                    strategy['query'],
                    max_results=100  # Get more per strategy, will filter later
                )
                
                # Convert to dict and add strategy info to each paper
                paper_dicts = []
                for paper in papers:
                    paper_dict = paper.dict() if hasattr(paper, 'dict') else paper.__dict__
                    paper_dict['discovery_strategy'] = strategy['strategy_type']
                    paper_dict['strategy_reasoning'] = strategy['reasoning']
                    paper_dicts.append(paper_dict)
                
                return paper_dicts
            except:
                return []
        
        # Execute all searches in parallel
        all_results = await asyncio.gather(*[
            search_with_strategy(strategy) for strategy in strategies
        ])
        
        # Flatten and deduplicate
        seen_ids = set()
        unique_papers = []
        for papers in all_results:
            for paper in papers:
                paper_id = paper.get('id') or paper.get('paper_id')
                if paper_id not in seen_ids:
                    seen_ids.add(paper_id)
                    unique_papers.append(paper)
        
        return unique_papers
    
    async def _analyze_and_rank_papers(
        self,
        papers: List[Dict[str, Any]],
        request: IntelligentSearchRequest,
        context: ResearchContext
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Use Llama 4's long context to analyze and rank papers"""
        
        # Prepare paper summaries for analysis
        paper_summaries = []
        for i, paper in enumerate(papers[:50]):  # Analyze up to 50 papers
            paper_summaries.append({
                'index': i,
                'title': paper.get('title'),
                'abstract': paper.get('abstract', '')[:500],
                'year': paper.get('year'),
                'authors': paper.get('authors', [])[:3],
                'discovery_strategy': paper.get('discovery_strategy')
            })
        
        prompt = f"""
        Analyze these {len(paper_summaries)} papers for the research question:
        "{request.research_question}"
        
        User is looking for:
        - Foundational papers: {request.include_foundational}
        - Recent advances: {request.include_recent}
        - Methodology focus: {request.methodology_focus or 'any'}
        - Exclude topics: {', '.join(request.exclude_topics)}
        
        Papers to analyze:
        {json.dumps(paper_summaries, indent=2)}
        
        Provide a JSON response with:
        1. "ranked_indices": Array of paper indices in order of relevance (most relevant first)
        2. "relevance_scores": Object mapping index to score (0-100)
        3. "insights": Object with:
           - "key_themes": Array of main themes found
           - "methodology_patterns": Array of common methodologies
           - "research_gaps": Array of identified gaps
           - "suggested_refinements": Array of search refinement suggestions
           - "related_areas": Array of related research areas to explore
           - "confidence_score": Overall confidence in results (0-1)
        
        Consider relevance, quality, foundational importance, and methodology alignment.
        """
        
        try:
            response = await self.llama_client.generate_response(prompt)
            analysis = json.loads(response)
            
            # Apply rankings to papers
            ranked_papers = []
            for idx in analysis.get('ranked_indices', []):
                if idx < len(papers):
                    paper = papers[idx].copy()
                    paper['relevance_score'] = analysis['relevance_scores'].get(str(idx), 50)
                    paper['llama_reasoning'] = f"Ranked #{len(ranked_papers)+1} for relevance to research question"
                    ranked_papers.append(paper)
            
            return ranked_papers, analysis.get('insights', {})
            
        except:
            # Fallback: return papers as-is
            return papers, {
                'confidence_score': 0.5,
                'key_themes': ['Unable to analyze'],
                'suggested_refinements': ['Try a more specific search']
            }
    
    async def _save_search_session(
        self,
        user_id: UUID,
        request: IntelligentSearchRequest,
        strategies: List[Dict[str, Any]],
        all_papers: List[Dict[str, Any]],
        ranked_papers: List[Dict[str, Any]],
        insights: Dict[str, Any]
    ):
        """Save the search session for future reference"""
        try:
            session_data = {
                'user_id': str(user_id),
                'research_question': request.research_question,
                'knowledge_base_id': str(request.knowledge_base_id) if request.knowledge_base_id else None,
                'query_strategies': strategies,
                'candidate_papers': [
                    {
                        'paper_id': p.get('paper_id'),
                        'title': p.get('title'),
                        'discovery_strategy': p.get('discovery_strategy')
                    }
                    for p in all_papers[:100]  # Store up to 100 candidates
                ],
                'ranked_papers': [
                    {
                        'paper_id': p.get('paper_id'),
                        'title': p.get('title'),
                        'relevance_score': p.get('relevance_score', 0)
                    }
                    for p in ranked_papers[:request.max_papers]
                ],
                'research_insights': insights,
                'total_candidates': len(all_papers),
                'max_papers': request.max_papers,
                'confidence_score': insights.get('confidence_score', 0.5)
            }
            
            self.supabase.table('intelligent_search_sessions').insert(session_data).execute()
        except Exception as e:
            print(f"Error saving search session: {e}") 