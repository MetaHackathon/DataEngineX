import httpx
import xml.etree.ElementTree as ET
from typing import List
from time import sleep
import uuid
from datetime import datetime, timedelta

from app.models.paper import PaperResponse
from app.utils.config import Config

class ArxivService:
    def __init__(self):
        self.base_url = Config.ARXIV_BASE_URL
        self.headers = {
            'User-Agent': Config.USER_AGENT
        }
        self.timeout = Config.API_TIMEOUT
    
    async def search(
        self,
        query: str,
        start: int = 0,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending"
    ) -> List[PaperResponse]:
        """Search ArXiv for papers based on query parameters"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Don't add 'all:' prefix if query already contains search terms
            search_query = query if any(term in query for term in ['cat:', 'submittedDate:']) else f'all:{query}'
            
            query_params = {
                'search_query': search_query,
                'start': start,
                'max_results': max_results,
                'sortBy': sort_by,
                'sortOrder': sort_order
            }
            
            print(f"ArXiv API query params: {query_params}")
            
            response = await client.get(self.base_url, params=query_params, headers=self.headers)
            
            if response.status_code == 429:
                await sleep(Config.RATE_LIMIT_DELAY)
                response = await client.get(self.base_url, params=query_params, headers=self.headers)
            
            response.raise_for_status()
            print(f"ArXiv API response status: {response.status_code}")
            
            return self._parse_response(response.text)
    
    async def get_recommended_papers(self, limit: int = 10) -> List[PaperResponse]:
        """Get recommended papers in CS and ML"""
        search_query = "cat:cs.AI OR cat:cs.LG OR cat:cs.ML OR cat:stat.ML"
        print(f"Recommended papers query: {search_query}")
        
        papers = await self.search(
            query=search_query,
            max_results=limit,
            sort_by="submittedDate",
            sort_order="descending"
        )
        print(f"Found {len(papers)} recommended papers")
        return papers
    
    async def get_trending_papers(self, limit: int = 10) -> List[PaperResponse]:
        """Get trending papers from the last month"""
        last_month = datetime.now() - timedelta(days=30)
        date_str = last_month.strftime('%Y%m%d')
        
        search_query = f"(cat:cs.AI OR cat:cs.LG OR cat:cs.ML OR cat:stat.ML) AND submittedDate:[{date_str}0000 TO 99991231235959]"
        print(f"Trending papers query: {search_query}")
        
        papers = await self.search(
            query=search_query,
            max_results=limit,
            sort_by="submittedDate",
            sort_order="descending"
        )
        print(f"Found {len(papers)} trending papers")
        return papers
    
    def _parse_response(self, response_text: str) -> List[PaperResponse]:
        """Parse ArXiv XML response into PaperResponse objects"""
        try:
            root = ET.fromstring(response_text)
        except ET.ParseError as e:
            print(f"ArXiv API response text: {response_text}")
            raise Exception(f"Failed to parse arXiv response: {str(e)}")
        
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'
        }
        
        papers = []
        for entry in root.findall('atom:entry', ns):
            try:
                paper = self._parse_entry(entry, ns)
                if paper:
                    papers.append(paper)
            except Exception as e:
                print(f"Error processing entry: {str(e)}")
                continue
        
        return papers
    
    def _parse_entry(self, entry, ns) -> PaperResponse:
        """Parse a single ArXiv entry into a PaperResponse"""
        # Extract authors
        authors = [author.find('atom:name', ns).text 
                  for author in entry.findall('atom:author', ns)]
        
        # Extract and clean title
        title_elem = entry.find('atom:title', ns)
        title = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else "No title"
        
        # Extract and clean abstract
        summary_elem = entry.find('atom:summary', ns)
        abstract = summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None else None
        
        # Extract arXiv ID and create URL
        id_elem = entry.find('atom:id', ns)
        arxiv_id = id_elem.text.split('/abs/')[-1] if id_elem is not None else None
        url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None
        
        # Extract published date and convert to year
        published_elem = entry.find('atom:published', ns)
        year = int(published_elem.text[:4]) if published_elem is not None else None
        
        # Extract categories for topics
        categories = entry.findall('atom:category', ns)
        topics = [cat.get('term') for cat in categories if cat.get('term')]
        
        # Determine impact based on certain criteria
        is_recent = year and year >= Config.RECENT_YEAR_THRESHOLD
        has_major_category = any(topic in Config.MAJOR_CATEGORIES for topic in topics)
        impact = "high" if is_recent and has_major_category else "low"
        
        return PaperResponse(
            id=arxiv_id or str(uuid.uuid4()),
            title=title,
            authors=authors,
            abstract=abstract,
            year=year or 2024,
            citations=0,
            impact=impact,
            url=url or "",
            topics=topics,
            institution=None
        ) 