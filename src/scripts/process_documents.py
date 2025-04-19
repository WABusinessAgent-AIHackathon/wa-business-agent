import logging
from ..knowledge_base.document_processor import DocumentProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_small_business_guide():
    """Process and add the Small Business Guide PDF to the knowledge base."""
    processor = DocumentProcessor()
    
    try:
        # Process the Small Business Guide
        document = processor.process_pdf_url(
            url="https://www.business.wa.gov/Portals/_business/VersionedDocuments/Business_Publications/small_business_guide.pdf",
            document_id="wa_small_business_guide",
            title="Washington Small Business Guide",
            category="guide"
        )
        
        logger.info(f"Successfully processed document: {document['title']}")
        logger.info(f"Pages: {document['page_count']}")
        logger.info(f"Content length: {len(document['content'])} characters")
        
        # Test search functionality
        test_queries = [
            "business license",
            "taxes",
            "minimum wage",
            "insurance"
        ]
        
        logger.info("\nTesting search functionality:")
        for query in test_queries:
            results = processor.search_documents(query)
            logger.info(f"Query '{query}' found {len(results)} matches")
            
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
    finally:
        processor.close()

if __name__ == "__main__":
    process_small_business_guide() 