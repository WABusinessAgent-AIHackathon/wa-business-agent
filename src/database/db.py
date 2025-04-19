import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import csv

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "data/wa_business.db", json_path: str = "data/content"):
        """Initialize database connection and create necessary tables."""
        # Ensure directories exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(json_path, exist_ok=True)
        
        self.db_path = db_path
        self.json_path = json_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary database tables if they don't exist."""
        with self.conn:
            # FAQs table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS faqs (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content_file TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Links table for FAQs
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    faq_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    value TEXT NOT NULL,
                    type TEXT NOT NULL,
                    FOREIGN KEY (faq_id) REFERENCES faqs (id)
                )
            """)

            # Resource links table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS resource_links (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    aria_label TEXT,
                    category TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Documents table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content_file TEXT NOT NULL,
                    page_count INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def save_faq(self, faq: Dict[str, Any]) -> None:
        """Save or update a FAQ entry."""
        faq_id = faq['metadata']['id']
        content_file = f"faq_{faq_id}.json"
        
        # Save full content to JSON file
        content = {
            'answer': faq['answer'],
            'html_answer': faq['html_answer']
        }
        with open(os.path.join(self.json_path, content_file), 'w') as f:
            json.dump(content, f, indent=2)
        
        # Save structured data to SQLite
        with self.conn:
            # Update or insert FAQ
            self.conn.execute("""
                INSERT OR REPLACE INTO faqs (id, question, category, content_file, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (faq_id, faq['question'], faq['category'], content_file))
            
            # Delete old links
            self.conn.execute("DELETE FROM links WHERE faq_id = ?", (faq_id,))
            
            # Insert new links
            for link in faq['links']:
                self.conn.execute("""
                    INSERT INTO links (faq_id, text, value, type)
                    VALUES (?, ?, ?, ?)
                """, (faq_id, link['text'], link['value'], link['type']))
    
    def get_faq(self, faq_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a FAQ by ID."""
        with self.conn:
            # Get FAQ data
            faq_row = self.conn.execute("""
                SELECT * FROM faqs WHERE id = ?
            """, (faq_id,)).fetchone()
            
            if not faq_row:
                return None
            
            # Get links
            links = self.conn.execute("""
                SELECT text, value, type FROM links WHERE faq_id = ?
            """, (faq_id,)).fetchall()
            
            # Get content from JSON file
            with open(os.path.join(self.json_path, faq_row['content_file'])) as f:
                content = json.load(f)
            
            return {
                'question': faq_row['question'],
                'answer': content['answer'],
                'html_answer': content['html_answer'],
                'category': faq_row['category'],
                'links': [dict(link) for link in links],
                'metadata': {
                    'id': faq_row['id'],
                    'created_at': faq_row['created_at'],
                    'updated_at': faq_row['updated_at']
                }
            }
    
    def get_all_faqs(self) -> List[Dict[str, Any]]:
        """Retrieve all FAQs."""
        with self.conn:
            faq_rows = self.conn.execute("SELECT id FROM faqs").fetchall()
            return [self.get_faq(row['id']) for row in faq_rows]
    
    def get_faqs_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Retrieve FAQs by category."""
        with self.conn:
            faq_rows = self.conn.execute("""
                SELECT id FROM faqs WHERE category = ?
            """, (category,)).fetchall()
            return [self.get_faq(row['id']) for row in faq_rows]
    
    def save_resource_link(self, resource: Dict[str, Any]) -> None:
        """Save or update a resource link entry."""
        resource_id = resource.get('id') or resource['title'].lower().replace(' ', '_')
        
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO resource_links 
                (id, title, url, aria_label, category, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                resource_id,
                resource['title'],
                resource['url'],
                resource.get('aria_label', ''),
                resource['category']
            ))

    def get_resource_link(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a resource link by ID."""
        with self.conn:
            row = self.conn.execute("""
                SELECT * FROM resource_links WHERE id = ?
            """, (resource_id,)).fetchone()
            
            if not row:
                return None
            
            return {
                'id': row['id'],
                'title': row['title'],
                'url': row['url'],
                'aria_label': row['aria_label'],
                'category': row['category'],
                'metadata': {
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            }

    def get_all_resource_links(self) -> List[Dict[str, Any]]:
        """Retrieve all resource links."""
        with self.conn:
            rows = self.conn.execute("SELECT * FROM resource_links").fetchall()
            return [{
                'id': row['id'],
                'title': row['title'],
                'url': row['url'],
                'aria_label': row['aria_label'],
                'category': row['category'],
                'metadata': {
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            } for row in rows]

    def get_resource_links_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Retrieve resource links by category."""
        with self.conn:
            rows = self.conn.execute("""
                SELECT * FROM resource_links WHERE category = ?
            """, (category,)).fetchall()
            return [{
                'id': row['id'],
                'title': row['title'],
                'url': row['url'],
                'aria_label': row['aria_label'],
                'category': row['category'],
                'metadata': {
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            } for row in rows]

    def export_resource_links_to_csv(self, csv_path: str = "data/resource_links.csv") -> None:
        """Export all resource links to a CSV file."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        # Get all resource links
        links = self.get_all_resource_links()
        
        # Define CSV headers
        headers = ['id', 'title', 'url', 'aria_label', 'category', 'created_at', 'updated_at']
        
        try:
            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for link in links:
                    # Flatten the metadata into the main dict
                    row = {
                        'id': link['id'],
                        'title': link['title'],
                        'url': link['url'],
                        'aria_label': link['aria_label'],
                        'category': link['category'],
                        'created_at': link['metadata']['created_at'],
                        'updated_at': link['metadata']['updated_at']
                    }
                    writer.writerow(row)
            
            logger.info(f"Successfully exported {len(links)} resource links to {csv_path}")
        except Exception as e:
            logger.error(f"Error exporting resource links to CSV: {str(e)}")
            raise
    
    def save_document(self, document: Dict[str, Any]) -> None:
        """Save or update a document entry."""
        document_id = document['id']
        content_file = f"doc_{document_id}.json"
        
        # Save full content and metadata to JSON file
        content = {
            'content': document['content'],
            'metadata': document['metadata']
        }
        with open(os.path.join(self.json_path, content_file), 'w') as f:
            json.dump(content, f, indent=2)
        
        # Save structured data to SQLite
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO documents 
                (id, title, url, category, content_file, page_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                document_id,
                document['title'],
                document['url'],
                document['category'],
                content_file,
                document['page_count']
            ))
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID."""
        with self.conn:
            row = self.conn.execute("""
                SELECT * FROM documents WHERE id = ?
            """, (document_id,)).fetchone()
            
            if not row:
                return None
            
            # Get content from JSON file
            with open(os.path.join(self.json_path, row['content_file'])) as f:
                content = json.load(f)
            
            return {
                'id': row['id'],
                'title': row['title'],
                'url': row['url'],
                'category': row['category'],
                'content': content['content'],
                'page_count': row['page_count'],
                'metadata': content['metadata'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
    
    def get_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Retrieve all documents in a category."""
        with self.conn:
            rows = self.conn.execute("""
                SELECT id FROM documents WHERE category = ?
            """, (category,)).fetchall()
            return [self.get_document(row['id']) for row in rows]
    
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """Search through document content."""
        results = []
        with self.conn:
            # Get all documents
            rows = self.conn.execute("SELECT id, content_file FROM documents").fetchall()
            
            # Search through each document's content
            for row in rows:
                with open(os.path.join(self.json_path, row['content_file'])) as f:
                    content = json.load(f)
                    
                    # If query is found in content, add to results
                    if query.lower() in content['content'].lower():
                        results.append(self.get_document(row['id']))
        
        return results
    
    def close(self):
        """Close the database connection."""
        self.conn.close() 