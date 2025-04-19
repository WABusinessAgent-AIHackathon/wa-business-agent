# Washington Business Agent

A FastAPI-based AI assistant that provides information and guidance about starting and running a business in Washington State. The application combines real-time data fetching, document processing, and natural language understanding to provide accurate and contextual responses about Washington State business regulations and requirements.

## Features

- 🤖 AI-powered chat interface for business inquiries
- 💼 Business license fee information and calculations
- 💵 Location-based minimum wage lookup
- 🚀 Step-by-step guidance for starting a business
- 🔗 Curated essential resource links
- 📊 Real-time data fetching from official sources
- 📄 PDF document processing and knowledge base
- 🕷️ Automated resource link scraping and categorization
- 🔍 Vector-based semantic search for accurate information retrieval

## Prerequisites

- Python 3.8 or higher
- Git
- OpenAI API key
- GitHub token (for accessing certain resources)
- Azure endpoint (optional, for enhanced search capabilities)

## Installation and Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/WABusinessAgent-AIHackathon/wa-business-agent.git
   cd wa-business-agent
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   # On macOS/Linux:
   python -m venv venv
   source venv/bin/activate

   # On Windows:
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Required Packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file in the project root with the following:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   GITHUB_TOKEN=your_github_token
   AZURE_ENDPOINT=your_azure_endpoint
   ```

## Running the Application

1. **Initialize the Knowledge Base**:
   ```bash
   python src/scripts/populate_vector_store.py
   ```

2. **Start the Application**:
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Access the Application**:
   - Web Interface: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - Alternative API Documentation: `http://localhost:8000/redoc`

## API Endpoints

- `GET /` - Main web interface
- `POST /api/chat` - Chat endpoint for business inquiries
- `GET /api/fees` - Business license fee information
- `GET /api/minimum-wage/{location}` - Minimum wage lookup by location
- `GET /api/starting-steps` - Steps to start a business
- `GET /api/essential-links` - Important resource links

## Features in Detail

### 1. AI-Powered Chat Interface
- Natural language understanding for business inquiries
- Context-aware responses based on Washington State regulations
- Real-time information fetching and validation

### 2. Knowledge Base
- Vector-based document storage using ChromaDB
- PDF processing capabilities
- Semantic search for accurate information retrieval
- Automated resource categorization

### 3. Data Sources
- Official Washington State business resources
- Department of Revenue documentation
- Labor and Industries regulations
- Municipal codes and requirements

### 4. Real-time Updates
- Dynamic minimum wage calculations
- Current business license fees
- Updated regulatory requirements

## Project Structure

```
wa-business-agent/
├── data/                      # Data storage
│   ├── vector_db/            # Vector database storage
│   ├── documents/            # Processed documents
│   ├── content/              # JSON content storage
│   └── cache/                # Cache storage
├── src/                      # Source code
│   ├── agent/               # Business agent logic
│   │   └── business_agent.py
│   ├── database/            # Database operations
│   │   └── db.py
│   ├── knowledge_base/      # Knowledge base components
│   │   ├── document_processor.py
│   │   ├── vector_store.py
│   │   └── wa_scraper.py
│   ├── scripts/             # Utility scripts
│   │   └── populate_vector_store.py
│   └── main.py             # FastAPI application
├── templates/               # HTML templates
├── static/                 # Static files
├── tests/                  # Test files
├── requirements.txt        # Python dependencies
└── .env                   # Environment variables
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Washington State Department of Revenue
- Washington State Department of Labor & Industries
- City of Seattle
- OpenAI
- FastAPI team

## Contact

Project Link: [https://github.com/WABusinessAgent-AIHackathon/wa-business-agent](https://github.com/WABusinessAgent-AIHackathon/wa-business-agent) 