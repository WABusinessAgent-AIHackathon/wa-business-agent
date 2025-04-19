import requests
import PyPDF2
import io
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..database.db import Database

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        
    def process_pdf_url(self, url: str, document_id: str, title: str, category: str = "guide") -> Dict[str, Any]:
        """Download and process a PDF document from a URL."""
        try:
            # Download the PDF
            logger.info(f"Downloading PDF from {url}")
            response = requests.get(url)
            response.raise_for_status()
            
            # Create a PDF reader object
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from all pages
            content = []
            for page in pdf_reader.pages:
                content.append(page.extract_text())
            
            # Create document metadata
            document = {
                'id': document_id,
                'title': title,
                'url': url,
                'category': category,
                'content': '\n'.join(content),
                'page_count': len(pdf_reader.pages),
                'metadata': {
                    'source': 'wa_business_gov',
                    'document_type': 'pdf',
                    'processed_at': datetime.now().isoformat()
                }
            }
            
            # Save to database
            self.db.save_document(document)
            
            logger.info(f"Successfully processed PDF document: {title}")
            return document
            
        except Exception as e:
            logger.error(f"Error processing PDF document: {str(e)}")
            raise
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID."""
        return self.db.get_document(document_id)
    
    def get_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Retrieve all documents in a category."""
        return self.db.get_documents_by_category(category)
    
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """Search through document content."""
        return self.db.search_documents(query)
    
    def close(self):
        """Close database connection."""
        self.db.close() 