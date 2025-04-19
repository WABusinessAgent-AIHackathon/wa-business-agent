import os
import sys
import logging
from datetime import datetime
from typing import List, Dict

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.knowledge_base.vector_store import VectorStore
from src.knowledge_base.wa_scraper import WABusinessScraper
from src.knowledge_base.document_processor import DocumentProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_faqs(vector_store: VectorStore, scraper: WABusinessScraper) -> None:
    """Process and store FAQs in the vector store."""
    try:
        faqs = scraper.get_faqs()
        for idx, faq in enumerate(faqs):
            metadata = {
                "type": "faq",
                "category": faq.get("category", "general"),
                "added_at": datetime.now().isoformat()
            }
            vector_store.add_faq(
                question=faq["question"],
                answer=faq["answer"],
                metadata=metadata,
                faq_id=f"faq_{idx}"
            )
        logger.info(f"Added {len(faqs)} FAQs to vector store")
    except Exception as e:
        logger.error(f"Error processing FAQs: {e}")
        raise

def process_resource_links(vector_store: VectorStore, scraper: WABusinessScraper) -> None:
    """Process and store resource links in the vector store."""
    try:
        links = scraper.get_resource_links()
        for idx, link in enumerate(links):
            metadata = {
                "type": "resource_link",
                "category": link.get("category", "general"),
                "url": link["url"],
                "added_at": datetime.now().isoformat()
            }
            vector_store.add_document(
                text=f"Title: {link['title']}\nDescription: {link.get('description', '')}\nURL: {link['url']}",
                metadata=metadata,
                doc_id=f"resource_{idx}",
                collection_name="wa_business_docs"
            )
        logger.info(f"Added {len(links)} resource links to vector store")
    except Exception as e:
        logger.error(f"Error processing resource links: {e}")
        raise

def process_business_guide(vector_store: VectorStore, doc_processor: DocumentProcessor) -> None:
    """Process the Washington Small Business Guide PDF."""
    guide_url = "https://www.business.wa.gov/Portals/_business/VersionedDocuments/Business_Publications/small_business_guide.pdf"
    try:
        sections = doc_processor.process_pdf_url(
            url=guide_url,
            document_id="wa_small_business_guide",
            title="Washington Small Business Guide"
        )
        if sections:
            logging.info("Successfully processed business guide")
            return True
    except Exception as e:
        logging.error(f"Error processing business guide: {str(e)}")
        return False

def process_forms(vector_store: VectorStore) -> None:
    """Add common business forms to the vector store."""
    forms = [
        {
            "name": "Business License Application",
            "fields": [
                {"name": "UBI Number", "type": "text", "required": True},
                {"name": "Business Name", "type": "text", "required": True},
                {"name": "Business Structure", "type": "select", "required": True},
                {"name": "Physical Location", "type": "address", "required": True},
                {"name": "Business Activities", "type": "multiselect", "required": True}
            ],
            "instructions": "Complete this form to apply for your Washington State Business License"
        },
        {
            "name": "Trade Name Registration",
            "fields": [
                {"name": "Business Name", "type": "text", "required": True},
                {"name": "UBI Number", "type": "text", "required": True},
                {"name": "Trade Name", "type": "text", "required": True}
            ],
            "instructions": "Use this form to register a trade name (DBA) for your business"
        }
    ]
    
    for idx, form in enumerate(forms):
        vector_store.add_form(
            form_name=form["name"],
            form_fields=form["fields"],
            instructions=form["instructions"],
            form_id=f"form_{idx}"
        )
    logger.info(f"Added {len(forms)} forms to vector store")

def main():
    """Main function to populate the vector store."""
    try:
        # Initialize components
        vector_store = VectorStore()
        scraper = WABusinessScraper()
        doc_processor = DocumentProcessor()
        
        # Process different types of content
        process_faqs(vector_store, scraper)
        process_resource_links(vector_store, scraper)
        process_business_guide(vector_store, doc_processor)
        process_forms(vector_store)
        
        logger.info("Successfully populated vector store")
        
    except Exception as e:
        logger.error(f"Error populating vector store: {e}")
        raise

if __name__ == "__main__":
    main() 