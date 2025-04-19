import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, persist_directory: str = "data/vector_db"):
        """Initialize the vector store with ChromaDB."""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB with persistence using new client format
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use sentence-transformers for embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Create collections for different types of content
        self.docs_collection = self.client.get_or_create_collection(
            name="wa_business_docs",
            embedding_function=self.embedding_function
        )
        
        self.faqs_collection = self.client.get_or_create_collection(
            name="wa_business_faqs",
            embedding_function=self.embedding_function
        )
        
        self.forms_collection = self.client.get_or_create_collection(
            name="wa_business_forms",
            embedding_function=self.embedding_function
        )

    def add_document(self, 
                    text: str, 
                    metadata: Dict, 
                    doc_id: str,
                    collection_name: str = "wa_business_docs") -> None:
        """Add a document to the vector store."""
        try:
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            # Add document with metadata
            collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            logger.info(f"Added document {doc_id} to collection {collection_name}")
            
        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
            raise

    def search(self, 
               query: str, 
               collection_name: str = "wa_business_docs",
               n_results: int = 5,
               metadata_filter: Optional[Dict] = None) -> List[Dict]:
        """Search for similar documents using semantic search."""
        try:
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            # Perform search with optional metadata filtering
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=metadata_filter
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None,
                    'id': results['ids'][0][i]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise

    def add_faq(self, question: str, answer: str, metadata: Dict, faq_id: str) -> None:
        """Add an FAQ to the vector store."""
        text = f"Question: {question}\nAnswer: {answer}"
        self.add_document(text, metadata, faq_id, "wa_business_faqs")

    def add_form(self, 
                form_name: str, 
                form_fields: List[Dict], 
                instructions: str,
                form_id: str) -> None:
        """Add a form template to the vector store."""
        text = f"Form: {form_name}\nInstructions: {instructions}\nFields: {str(form_fields)}"
        metadata = {
            "type": "form",
            "name": form_name,
            "field_count": len(form_fields),
            "added_at": datetime.now().isoformat()
        }
        self.add_document(text, metadata, form_id, "wa_business_forms")

    def search_forms(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search for relevant forms based on user query."""
        return self.search(query, "wa_business_forms", n_results)

    def search_faqs(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant FAQs based on user query."""
        return self.search(query, "wa_business_faqs", n_results)

    def get_similar_documents(self, text: str, n_results: int = 5) -> List[Dict]:
        """Find similar documents to the given text."""
        return self.search(text, "wa_business_docs", n_results)

    def delete_document(self, doc_id: str, collection_name: str = "wa_business_docs") -> None:
        """Delete a document from the vector store."""
        try:
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            collection.delete(ids=[doc_id])
            logger.info(f"Deleted document {doc_id} from collection {collection_name}")
        except Exception as e:
            logger.error(f"Error deleting document from vector store: {e}")
            raise

    def clear_collection(self, collection_name: str) -> None:
        """Clear all documents from a collection."""
        try:
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            collection.delete()
            logger.info(f"Cleared collection {collection_name}")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise 