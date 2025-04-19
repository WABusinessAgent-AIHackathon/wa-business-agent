from src.knowledge_base.wa_scraper import WABusinessScraper
import os
import json
import csv
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_separator():
    print("\n" + "="*50 + "\n")

def export_faqs_to_csv(faqs, output_file):
    """Export FAQs to a CSV file for better readability."""
    fieldnames = ['id', 'question', 'answer', 'links']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for faq in faqs:
            # Format links as a readable string
            links_str = ' | '.join([f"{link['text']} ({link['value']})" for link in faq['links']])
            
            writer.writerow({
                'id': faq['metadata'].get('id', ''),
                'question': faq['question'],
                'answer': faq['answer'],
                'links': links_str
            })

def export_faqs_to_json(faqs, output_dir):
    """Export each FAQ as a separate JSON document."""
    os.makedirs(output_dir, exist_ok=True)
    
    for faq in faqs:
        faq_id = faq['metadata'].get('id', 'faq_' + str(hash(faq['question'])))
        output_file = os.path.join(output_dir, f"{faq_id}.json")
        
        # Create a clean FAQ document
        faq_doc = {
            'id': faq_id,
            'question': faq['question'],
            'answer': faq['answer'],
            'links': faq['links']
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(faq_doc, f, indent=2, ensure_ascii=False)

def main():
    # Initialize scraper
    scraper = WABusinessScraper()
    
    try:
        # 1. Test scraping
        print("1. Scraping FAQs...")
        faqs = scraper.get_faqs()
        print(f"Scraped {len(faqs)} FAQs")
        
        # Export to CSV
        csv_path = os.path.join('data', 'faqs.csv')
        export_faqs_to_csv(faqs, csv_path)
        print(f"\nExported FAQs to: {csv_path}")
        
        # Export to JSON
        json_dir = os.path.join('data', 'faqs')
        export_faqs_to_json(faqs, json_dir)
        print(f"Exported individual FAQ documents to: {json_dir}")
        
        print_separator()
        
        # 2. Print example FAQ
        if faqs:
            first_faq = faqs[0]
            print("Example FAQ:")
            print(f"Question: {first_faq['question']}")
            print(f"Answer: {first_faq['answer'][:200]}...")  # First 200 chars
            print(f"Number of links: {len(first_faq['links'])}")
            if first_faq['links']:
                print("\nExample link:")
                print(f"Text: {first_faq['links'][0]['text']}")
                print(f"URL: {first_faq['links'][0]['value']}")
        
        print_separator()
        
        # 3. Verify file storage
        print("3. Verifying file storage...")
        print(f"CSV file exists: {os.path.exists(csv_path)}")
        print(f"JSON directory exists: {os.path.exists(json_dir)}")
        
        if os.path.exists(json_dir):
            json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
            print(f"Number of JSON files: {len(json_files)}")
            
            if json_files:
                print("\nExample JSON file contents:")
                with open(os.path.join(json_dir, json_files[0])) as f:
                    example_faq = json.load(f)
                    print(json.dumps(example_faq, indent=2))
        
    finally:
        # Clean up
        scraper.close()

def test_resource_links():
    scraper = WABusinessScraper()
    
    # Get the links
    links = scraper.get_resource_links()
    
    # Print summary
    logger.info(f"Found {len(links)} resource links")
    
    # Count by category
    categories = {}
    for link in links:
        cat = link['category']
        categories[cat] = categories.get(cat, 0) + 1
        logger.info(f"Found link: {link['title']} ({link['category']})")
    
    # Print category summary
    logger.info("\nCategory Summary:")
    for cat, count in categories.items():
        logger.info(f"{cat}: {count} links")

if __name__ == "__main__":
    main()
    test_resource_links() 