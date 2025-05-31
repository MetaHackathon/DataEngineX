# DataEngineX

A microservice for gathering research paper metadata from multiple APIs, starting with ArXiv. The service provides structured endpoints for searching, discovering trending papers, and accessing recommended foundational papers in computer science and machine learning.

## Features

- 🔍 **Search ArXiv Papers**: Full-text search with sorting and pagination
- 📈 **Trending Papers**: Discover recent papers from the last month
- ⭐ **Recommended Papers**: Curated foundational papers in CS/ML
- 🏗️ **Clean Architecture**: Model-Controller-Service pattern
- 📊 **Structured Response**: Consistent JSON format with metadata
- 🔧 **Configurable**: Environment-based configuration

## Architecture

```
DataEngineX/
├── app/
│   ├── models/          # Pydantic models for request/response
│   ├── controllers/     # Business logic and request handling
│   ├── services/        # External API integrations
│   └── utils/          # Configuration and utilities
├── main.py             # FastAPI application entry point
├── requirements.txt    # Python dependencies
└── README.md          # Project documentation
```

## Quick Start

### Prerequisites
- Python 3.8+
- pip

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

3. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`

## API Endpoints

### Search ArXiv Papers
```
GET /api/arxiv/search?query=machine learning&max_results=10
```

### Get Recommended Papers
```
GET /api/papers/recommended?limit=20
```

### Get Trending Papers
```
GET /api/papers/trending?limit=15
```

## Response Format

All endpoints return a list of papers with the following structure:

```json
{
  "id": "2301.00001",
  "title": "Paper Title",
  "abstract": "Paper abstract...",
  "authors": ["Author One", "Author Two"],
  "year": 2023,
  "citations": 0,
  "institution": null,
  "impact": "high",
  "url": "https://arxiv.org/pdf/2301.00001.pdf",
  "topics": ["cs.AI", "cs.LG"]
}
```

## Configuration

The application uses environment variables for configuration. Create a `.env` file:

```env
# Add any environment-specific configurations here
```

## Development

### Project Structure

- **Models** (`app/models/`): Pydantic models for data validation
- **Controllers** (`app/controllers/`): Handle HTTP requests and business logic
- **Services** (`app/services/`): Integration with external APIs (ArXiv, etc.)
- **Utils** (`app/utils/`): Configuration and utility functions

### Adding New Features

1. **New Models**: Add to `app/models/`
2. **New Services**: Add to `app/services/` for external API integrations
3. **New Endpoints**: Add controller methods and route them in `main.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Future Enhancements

- 📚 Integration with more academic databases (PubMed, IEEE, etc.)
- 🔍 Advanced search filters and faceted search
- 📊 Citation analysis and paper metrics
- 🤖 AI-powered paper recommendations
- 📈 Analytics and usage metrics
