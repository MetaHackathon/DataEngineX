from fastapi import FastAPI, HTTPException, Query
import httpx
from typing import Optional, List
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from time import sleep
import uuid
from datetime import datetime, timedelta

load_dotenv()

app = FastAPI(
    title="DataEngine",
    description="Microservice for gathering research paper metadata from multiple APIs",
    version="1.0.0"
)

class PaperResponse(BaseModel):
    id: str
    title: str
    abstract: Optional[str] = None
    authors: List[str]
    year: int
    citations: int = 0  # ArXiv doesn't provide citations, default to 0
    institution: Optional[str] = None
    impact: str = "low"  # We can determine this based on certain criteria
    url: str
    topics: List[str] = []

class ArxivQuery(BaseModel):
    search_query: str
    start: int = Field(default=0, ge=0)
    max_results: int = Field(default=10, ge=1, le=100)
    sort_by: str = Field(default="relevance", pattern="^(relevance|lastUpdatedDate|submittedDate)$")
    sort_order: str = Field(default="descending", pattern="^(ascending|descending)$")

@app.get("/")
async def root():
    return {"message": "Welcome to DataEngine API"}

async def search_arxiv_internal(
    query: str,
    start: int = 0,
    max_results: int = 10,
    sort_by: str = "relevance",
    sort_order: str = "descending"
) -> List[PaperResponse]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
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
            
            headers = {
                'User-Agent': 'DataEngine/1.0 (https://github.com/NeuxsAI/DataEngine)'
            }
            
            url = 'http://export.arxiv.org/api/query'
            response = await client.get(url, params=query_params, headers=headers)
            
            if response.status_code == 429:
                await sleep(1)
                response = await client.get(url, params=query_params, headers=headers)
            
            response.raise_for_status()
            print(f"ArXiv API response status: {response.status_code}")
            
            try:
                root = ET.fromstring(response.text)
            except ET.ParseError as e:
                print(f"ArXiv API response text: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse arXiv response: {str(e)}"
                )
            
            ns = {'atom': 'http://www.w3.org/2005/Atom',
                  'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'}
            
            papers = []
            for entry in root.findall('atom:entry', ns):
                try:
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
                    major_categories = {'cs.AI', 'cs.LG', 'cs.CL', 'stat.ML'}
                    is_recent = year and year >= 2020
                    has_major_category = any(topic in major_categories for topic in topics)
                    impact = "high" if is_recent and has_major_category else "low"
                    
                    papers.append(PaperResponse(
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
                    ))
                    
                except Exception as e:
                    print(f"Error processing entry: {str(e)}")
                    continue
            
            return papers
            
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"ArXiv API error: {str(e)}"
            )

@app.get("/api/arxiv/search", response_model=List[PaperResponse])
async def search_arxiv(
    query: str = Query(..., description="Search query (e.g., 'machine learning')"),
    start: int = Query(0, ge=0, description="Starting index"),
    max_results: int = Query(10, ge=1, le=100, description="Number of results to return"),
    sort_by: str = Query("relevance", pattern="^(relevance|lastUpdatedDate|submittedDate)$"),
    sort_order: str = Query("descending", pattern="^(ascending|descending)$")
):
    return await search_arxiv_internal(
        query=query,
        start=start,
        max_results=max_results,
        sort_by=sort_by,
        sort_order=sort_order
    )

@app.get("/api/papers/recommended", response_model=List[PaperResponse])
async def get_recommended_papers(
    limit: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """Return foundational papers in computer science and machine learning"""
    # Use proper ArXiv query syntax
    search_query = "cat:cs.AI OR cat:cs.LG OR cat:cs.ML OR cat:stat.ML"
    print(f"Recommended papers query: {search_query}")
    papers = await search_arxiv_internal(
        query=search_query,
        max_results=limit,
        sort_by="submittedDate",
        sort_order="descending"
    )
    print(f"Found {len(papers)} recommended papers")
    return papers

@app.get("/api/papers/trending", response_model=List[PaperResponse])
async def get_trending_papers(
    limit: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """Return trending papers from the last month in computer science and machine learning"""
    # Format date for last month
    last_month = datetime.now() - timedelta(days=30)
    date_str = last_month.strftime('%Y%m%d')
    
    # Use proper ArXiv query syntax
    search_query = f"(cat:cs.AI OR cat:cs.LG OR cat:cs.ML OR cat:stat.ML) AND submittedDate:[{date_str}0000 TO 99991231235959]"
    print(f"Trending papers query: {search_query}")
    papers = await search_arxiv_internal(
        query=search_query,
        max_results=limit,
        sort_by="submittedDate",
        sort_order="descending"
    )
    print(f"Found {len(papers)} trending papers")
    return papers

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
