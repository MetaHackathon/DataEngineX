"""
Llama API Client for AI-powered features in DataEngineX
"""

import os
import json
from typing import Dict, Any, Optional, List
from openai import OpenAI

class LlamaClient:
    """Client for interacting with Llama 4 API"""
    
    def __init__(self):
        self.api_key = os.getenv("LLAMA_API_KEY")
        
        if not self.api_key:
            print("Warning: LLAMA_API_KEY not found in environment variables. Using mock responses.")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.llama.com/v1"
            )
    
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a response from Llama 4"""
        
        if not self.client:
            return self._mock_response(prompt)
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Build completion kwargs
            completion_kwargs = {
                "model": "Llama-4-Maverick-17B-128E-Instruct-FP8",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Add response_format if provided (for structured JSON output)
            if response_format:
                completion_kwargs["response_format"] = response_format
            
            response = self.client.chat.completions.create(**completion_kwargs)
            
            # Handle Llama API response format
            if hasattr(response, 'completion_message') and response.completion_message:
                content = response.completion_message.get('content', {})
                if isinstance(content, dict) and 'text' in content:
                    return content['text'].strip()
                elif isinstance(content, str):
                    return content.strip()
            
            # Handle raw JSON response
            if hasattr(response, 'json') and callable(response.json):
                try:
                    json_response = response.json()
                    if isinstance(json_response, dict) and 'content' in json_response:
                        return json_response['content'].strip()
                    return json.dumps(json_response)
                except:
                    pass
            
            # Fallback for OpenAI-style response
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if isinstance(content, (dict, list)):
                    return json.dumps(content)
                return content.strip()
            
            print(f"Unexpected response structure: {response}")
            return self._mock_response(prompt)
                        
        except Exception as e:
            print(f"Error calling Llama API: {e}")
            return self._mock_response(prompt)
    
    async def analyze_paper(
        self,
        title: str,
        abstract: str,
        content: Optional[str] = None,
        analysis_type: str = "summary"
    ) -> Dict[str, Any]:
        """Analyze a research paper"""
        
        system_prompt = """You are an AI research assistant specializing in academic paper analysis. 
        Provide structured, insightful analysis that helps researchers understand key contributions, 
        methodology, and implications."""
        
        if analysis_type == "summary":
            prompt = f"""
            Please provide a comprehensive summary of this research paper:
            
            Title: {title}
            Abstract: {abstract}
            
            Include:
            1. Main research question/problem
            2. Key methodology
            3. Major findings
            4. Significance and implications
            5. Limitations
            """
        elif analysis_type == "methodology":
            prompt = f"""
            Analyze the methodology of this research paper:
            
            Title: {title}
            Abstract: {abstract}
            
            Focus on:
            1. Research design and approach
            2. Data collection methods
            3. Analysis techniques
            4. Strengths and weaknesses of the methodology
            5. Reproducibility considerations
            """
        elif analysis_type == "critique":
            prompt = f"""
            Provide a critical evaluation of this research paper:
            
            Title: {title}
            Abstract: {abstract}
            
            Address:
            1. Strengths of the research
            2. Potential weaknesses or limitations
            3. Clarity and organization
            4. Significance of contribution
            5. Suggestions for improvement
            """
        else:
            prompt = f"""
            Extract the key points from this research paper:
            
            Title: {title}
            Abstract: {abstract}
            
            Provide:
            1. Main contributions
            2. Key findings
            3. Important concepts
            4. Practical implications
            """
        
        response = await self.generate_response(prompt, system_prompt=system_prompt)
        
        return {
            "analysis": response,
            "type": analysis_type,
            "insights": self._extract_insights(response),
            "key_concepts": self._extract_concepts(response)
        }
    
    async def chat_with_paper(
        self,
        paper_title: str,
        paper_abstract: str,
        user_question: str,
        context: Optional[str] = None
    ) -> str:
        """Chat about a specific paper"""
        
        system_prompt = f"""You are helping a researcher understand this paper:
        
        Title: {paper_title}
        Abstract: {paper_abstract}
        
        Answer questions accurately based on the paper content. If you reference specific details,
        be clear about what you're citing. If something is unclear from the abstract alone,
        acknowledge this limitation."""
        
        prompt = user_question
        if context:
            prompt += f"\n\nAdditional context: {context}"
        
        return await self.generate_response(prompt, system_prompt=system_prompt)
    
    async def generate_insights(
        self,
        papers_data: List[Dict[str, Any]],
        knowledge_base_name: str
    ) -> Dict[str, Any]:
        """Generate insights for a knowledge base"""
        
        papers_summary = "\n".join([
            f"- {paper.get('title', 'Untitled')}: {paper.get('abstract', 'No abstract')[:200]}..."
            for paper in papers_data[:10]  # Limit for context length
        ])
        
        prompt = f"""
        Analyze this collection of research papers in the knowledge base "{knowledge_base_name}":
        
        {papers_summary}
        
        Please provide a JSON response with:
        1. "insights": Array of 3-5 key insights about the research area
        2. "trends": Array of 3-4 emerging trends identified
        3. "research_gaps": Array of 2-3 identified research gaps
        4. "key_connections": Array of 2-3 important connections between papers
        
        Focus on academic rigor and actionable insights.
        """
        
        response = await self.generate_response(prompt, max_tokens=1500)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "insights": [
                    "This knowledge base contains valuable research in an active area",
                    "Multiple approaches and methodologies are represented",
                    "There are opportunities for cross-pollination of ideas"
                ],
                "trends": [
                    "Emerging methodological approaches",
                    "Increasing focus on practical applications",
                    "Growing interdisciplinary connections"
                ],
                "research_gaps": [
                    "Areas for future empirical validation",
                    "Opportunities for larger-scale studies"
                ],
                "key_connections": [
                    "Shared theoretical foundations across papers",
                    "Complementary methodological approaches"
                ]
            }
    
    def _mock_response(self, prompt: str) -> str:
        """Provide mock responses when API is not available"""
        if "connections" in prompt.lower():
            # Mock response for connections analysis
            return json.dumps({
                "nodes": [
                    {
                        "id": "mock_paper_1",
                        "title": "Mock Paper 1",
                        "authors": ["Author 1"],
                        "year": 2023,
                        "citations": 100,
                        "qualityScore": 8.5,
                        "x": 400,
                        "y": 300,
                        "connections": 2
                    },
                    {
                        "id": "mock_paper_2",
                        "title": "Mock Paper 2",
                        "authors": ["Author 2"],
                        "year": 2022,
                        "citations": 50,
                        "qualityScore": 8.0,
                        "x": 600,
                        "y": 300,
                        "connections": 1
                    }
                ],
                "edges": [
                    {
                        "source": "mock_paper_1",
                        "target": "mock_paper_2",
                        "strength": 0.8
                    }
                ],
                "stats": {
                    "totalNodes": 2,
                    "totalConnections": 1,
                    "avgDegree": 1.0
                }
            })
        
        elif "summary" in prompt.lower():
            return """This research addresses an important problem in the field. The authors propose a novel methodology that shows promising results. Key findings include improved performance metrics and practical applications. The work contributes to our understanding of the domain and opens avenues for future research. Some limitations include the need for larger datasets and broader validation."""
        
        elif "methodology" in prompt.lower():
            return """The research employs a well-designed experimental approach. The methodology includes appropriate data collection procedures, robust analysis techniques, and proper controls. Strengths include the systematic approach and clear documentation. Areas for improvement might include larger sample sizes and additional validation studies."""
        
        elif "critique" in prompt.lower():
            return """This work makes a solid contribution to the field. Strengths include the novel approach, thorough analysis, and clear presentation. The research addresses an important problem with appropriate methodology. Potential limitations include scope constraints and the need for broader validation. Overall, this is valuable research that advances our understanding."""
        
        elif "analyze" in prompt.lower() or "insight" in prompt.lower():
            return """Based on the papers in this collection, several key themes emerge: innovative methodologies, practical applications, and theoretical advancements. There are opportunities for cross-disciplinary collaboration and further research in emerging areas. The work collectively represents significant progress in the field."""
        
        else:
            return """This is an interesting question about the research. Based on the paper content, there are several relevant points to consider. The authors address this topic through their methodology and findings. For more specific details, I'd recommend reviewing the full paper text and methodology sections."""
    
    def _extract_insights(self, text: str) -> List[str]:
        """Extract key insights from analysis text"""
        # Simple extraction - in production, this could be more sophisticated
        insights = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['insight', 'finding', 'key', 'important', 'significant']):
                cleaned = line.strip('- •').strip()
                if len(cleaned) > 10:
                    insights.append(cleaned)
        return insights[:5]  # Limit to top 5
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from analysis text"""
        # Simple concept extraction - in production, this could use NLP
        concepts = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['concept', 'approach', 'method', 'technique', 'theory']):
                cleaned = line.strip('- •').strip()
                if len(cleaned) > 5:
                    concepts.append(cleaned)
        return concepts[:8]  # Limit to top 8 