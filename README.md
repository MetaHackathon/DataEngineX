# DataEngineX

A unified microservice for research paper discovery and intelligent document processing. Combines ArXiv paper search with advanced RAG (Retrieval Augmented Generation) capabilities powered by **Chunkr AI**.

## 🚀 Features

### Paper Discovery
- 🔍 **Search ArXiv Papers**: Full-text search with sorting and pagination
- 📈 **Trending Papers**: Discover recent papers from the last month
- ⭐ **Recommended Papers**: Curated foundational papers in CS/ML

### RAG Processing (NEW!)
- 🤖 **Chunkr AI Integration**: Advanced document intelligence with layout analysis
- 🧠 **Intelligent Chunking**: Layout-aware document segmentation
- 🔍 **Semantic Search**: Search within paper content using processed chunks
- 📝 **Annotation Support**: Index and search through paper annotations
- 📊 **Multi-format Support**: PDFs, Word, Excel, PowerPoint, and images

### Architecture
- 🏗️ **Clean Architecture**: Model-Controller-Service pattern
- 📊 **Structured Response**: Consistent JSON format with metadata
- 🔧 **Configurable**: Environment-based configuration
- 🎯 **Demo Ready**: Perfect for hackathon demonstrations

## Architecture

```
DataEngineX/
├── app/
│   ├── models/              # Pydantic models for request/response
│   │   ├── paper.py         # ArXiv paper models
│   │   └── rag_models.py    # RAG-specific models
│   ├── controllers/         # Business logic and request handling
│   │   ├── paper_controller.py  # ArXiv paper operations
│   │   └── rag_controller.py    # RAG operations
│   ├── services/            # External API integrations
│   │   ├── arxiv_service.py     # ArXiv API integration
│   │   └── chunkr_service.py    # Chunkr AI integration
│   └── utils/              # Configuration and utilities
│       └── config.py        # Enhanced configuration
├── main.py                 # FastAPI application with all endpoints
├── requirements.txt        # Updated dependencies
└── README.md              # This file
```

## Quick Start

### Prerequisites
- Python 3.8+
- pip
- Chunkr AI API key (optional - demo mode available)
- Supabase account (for data storage)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/DataEngineX.git
cd DataEngineX
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create .env file
cp .env.example .env

# Edit .env with your credentials
CHUNKR_API_KEY=your_chunkr_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

4. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`

## API Endpoints

### 📚 Paper Discovery (Existing)

#### Search ArXiv Papers
```
GET /api/arxiv/search?query=machine learning&max_results=10
```

#### Get Recommended Papers
```
GET /api/papers/recommended?limit=20
```

#### Get Trending Papers
```
GET /api/papers/trending?limit=15
```

### 🤖 RAG Processing (New!)

#### Index Paper for RAG
```
POST /api/rag/papers/{paper_id}/index
{
  "paper_id": "2301.00001",
  "title": "Paper Title",
  "authors": ["Author One"],
  "pdf_url": "https://arxiv.org/pdf/2301.00001.pdf"
}
```

#### Search Within Paper
```
POST /api/rag/papers/{paper_id}/search
{
  "query": "neural networks",
  "limit": 5
}
```

#### Index Annotation
```
POST /api/rag/papers/{paper_id}/annotations/{annotation_id}
{
  "annotation_id": "note_1",
  "content": "Important finding about attention mechanisms",
  "user_id": "researcher_123"
}
```

#### Get System Stats
```
GET /api/rag/stats
```

### 🎯 Demo Workflow (Perfect for Hackathons!)

#### Complete End-to-End Demo
```
POST /api/demo/complete-workflow?query=transformers&paper_index=0&search_query=attention
```

This single endpoint demonstrates the entire workflow:
1. **Search ArXiv** for papers matching "transformers"
2. **Index the first paper** using Chunkr AI
3. **Search within the paper** for "attention"
4. **Return complete results** showing the full pipeline

## Configuration

The application uses environment variables for configuration. Create a `.env` file:

```env
# Chunkr AI Configuration
CHUNKR_API_KEY=your_chunkr_api_key

# Supabase Configuration  
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Optional: Custom settings
DEBUG=True
```

## What's New in v2.0

### 🆕 Chunkr AI Integration
- **Advanced Document Processing**: Layout-aware chunking instead of simple text splitting
- **Multi-format Support**: Process PDFs, Word docs, presentations, and images
- **OCR Capabilities**: Extract text from scanned documents
- **Vision Language Models**: Enhanced document understanding

### 🆕 Unified Service Architecture
- **Single Service**: Both paper discovery and RAG in one service
- **Reduced Complexity**: No more managing multiple microservices
- **Better Performance**: Eliminated network overhead between services
- **Shared Dependencies**: Unified FastAPI and Supabase integration

### 🆕 Demo-Ready Features
- **Complete Workflow Endpoint**: Perfect for live demonstrations
- **Fallback Demo Mode**: Works even without Chunkr API key
- **System Statistics**: Real-time stats for dashboards
- **Enhanced Documentation**: Better API docs and examples

## Development

### Adding New Features

1. **New Models**: Add to `app/models/rag_models.py`
2. **New Services**: Extend `app/services/chunkr_service.py`
3. **New Endpoints**: Add controller methods and route them in `main.py`

### Database Schema (Supabase)

```sql
-- Paper chunks table
CREATE TABLE paper_chunks (
  id SERIAL PRIMARY KEY,
  paper_id TEXT NOT NULL,
  chunk_id TEXT UNIQUE NOT NULL,
  content TEXT NOT NULL,
  page_number INTEGER,
  section TEXT,
  chunk_index INTEGER,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Annotations table
CREATE TABLE annotations (
  id TEXT PRIMARY KEY,
  paper_id TEXT NOT NULL,
  content TEXT NOT NULL,
  highlight_text TEXT,
  user_id TEXT,
  page_number INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎉 Perfect for Hackathons!

This unified service provides everything you need for an impressive research paper processing demo:

- **Quick Setup**: Get running in minutes
- **Demo Mode**: Works without external API keys
- **Complete Workflow**: End-to-end paper discovery and processing
- **Modern Tech Stack**: FastAPI, Chunkr AI, Supabase
- **Great Documentation**: Swagger UI for easy testing

## Future Enhancements

- 🌍 Integration with more academic databases (PubMed, IEEE, etc.)
- 🎯 Advanced search filters and faceted search
- 📈 Citation analysis and paper metrics
- 🤖 AI-powered paper recommendations based on content
- 📊 Analytics dashboard for usage metrics
- 🔍 Cross-paper semantic search capabilities
