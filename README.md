# Washington Business Agent

A FastAPI-based application that provides information and guidance about starting and running a business in Washington State. The application includes a chat interface, resource links, and various endpoints for business-related information.

## Features

- Interactive chat interface with AI-powered responses
- Business license fee information
- Minimum wage lookup by location
- Starting steps for new businesses
- Essential resource links
- Real-time data fetching from official sources
- PDF document processing and knowledge base
- Resource link scraping and categorization

## Prerequisites

- Python 3.8 or higher
- Git (optional, for cloning the repository)

## Installation and Setup

1. **Clone the Repository** (if using Git):
   ```bash
   git clone <repository-url>
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
   - Create a `.env` file in the project root
   - Add the following configuration:
     ```
     OPENAI_API_KEY=your_openai_api_key
     GITHUB_TOKEN=your_github_token
     AZURE_ENDPOINT=your_azure_endpoint
     ```

## Running the Application

1. **Start the Application**:
   ```bash
   # Navigate to the project directory (if not already there)
   cd /path/to/wa-business-agent

   # Start the FastAPI server
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the Application**:
   - Web Interface: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - Alternative API Documentation: `http://localhost:8000/redoc`

## Available Endpoints

- `/` - Main web interface
- `/api/chat` - Chat endpoint for business inquiries
- `/api/fees` - Business license fee information
- `/api/minimum-wage/{location}` - Minimum wage lookup by location
- `/api/starting-steps` - Steps to start a business
- `/api/essential-links` - Important resource links

## Using the Application

1. **Quick Access Menu**:
   - Business License Fees
   - Starting Steps
   - Essential Resources
   - Minimum Wage Information (WA State, Seattle, and other locations)

2. **Chat Interface**:
   - Ask questions about starting or running a business in Washington
   - Get real-time information from official sources
   - Access structured data about fees, requirements, and regulations

## Troubleshooting

1. **Port Already in Use**:
   ```bash
   # Try a different port
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
   ```

2. **Package Installation Issues**:
   ```bash
   # Update all packages
   pip install --upgrade -r requirements.txt
   ```

3. **Environment Variable Errors**:
   - Ensure `.env` file exists in the project root
   - Verify all required API keys are properly set
   - Check for any typos in the environment variable names

4. **Application Not Loading**:
   - Check if the server is running (terminal should show startup messages)
   - Verify you're using the correct URL and port
   - Check browser console for any JavaScript errors

## Stopping the Application

1. Press `Ctrl+C` in the terminal to stop the server
2. Deactivate the virtual environment:
   ```bash
   deactivate
   ```

## Project Structure

```
wa-business-agent/
├── data/                  # Data storage
├── src/                   # Source code
│   ├── agent/            # Business agent logic
│   ├── database/         # Database operations
│   ├── knowledge_base/   # Knowledge base and document processing
│   └── main.py          # FastAPI application
├── templates/            # HTML templates
├── static/              # Static files
├── tests/               # Test files
├── requirements.txt     # Python dependencies
└── .env                # Environment variables
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license information here]

## Contact

[Add your contact information here] 