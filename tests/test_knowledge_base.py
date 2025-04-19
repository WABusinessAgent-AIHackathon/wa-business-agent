import pytest
from datetime import datetime
import requests
from src.knowledge_base.wa_scraper import WABusinessScraper
from src.knowledge_base.static_knowledge import WABusinessKnowledge

@pytest.fixture
def scraper():
    return WABusinessScraper()

def test_minimum_wage(scraper):
    """Test minimum wage data retrieval."""
    wage_data = scraper.get_minimum_wage()
    assert isinstance(wage_data, dict)
    assert "washington" in wage_data
    assert wage_data["washington"] >= 16.28  # WA state minimum as of 2024
    assert all(isinstance(v, float) for v in wage_data.values())

def test_license_requirements(scraper):
    """Test license requirements retrieval."""
    requirements = scraper.get_license_requirements()
    assert isinstance(requirements, list)
    assert len(requirements) > 0
    assert any("endorsements" in req.lower() for req in requirements)
    assert any("employees" in req.lower() for req in requirements)
    assert any("sales tax" in req.lower() for req in requirements)

def test_fees(scraper):
    """Test fee structure retrieval."""
    fees = scraper.get_fees()
    assert isinstance(fees, dict)
    assert "new_business" in fees
    assert fees["new_business"] == 90.0
    assert "additional" in fees
    assert fees["additional"] == 19.0

def test_error_handling(scraper):
    """Test error handling with invalid URL."""
    original_url = scraper.base_url
    scraper.base_url = "https://invalid.url.that.doesnt.exist"
    
    # Test minimum wage fallback
    wage_data = scraper.get_minimum_wage()
    assert wage_data["washington"] == 16.28
    
    # Test license requirements fallback
    requirements = scraper.get_license_requirements()
    assert "Business requires city/state endorsements" in requirements
    
    # Test fees fallback
    fees = scraper.get_fees()
    assert fees["new_business"] == 90.0
    
    # Restore original URL
    scraper.base_url = original_url

def test_cache_functionality(scraper):
    """Test that caching works."""
    # First call should hit the website
    first_wage = scraper.get_minimum_wage()
    first_time = datetime.now()
    
    # Second call should use cache
    second_wage = scraper.get_minimum_wage()
    assert first_wage == second_wage
    
    # Clear cache and verify new fetch
    scraper.clear_cache()
    assert 'minimum_wage' not in scraper.cache

def test_last_updated(scraper):
    """Test last updated timestamp."""
    timestamp = scraper.get_last_updated()
    assert isinstance(timestamp, datetime)
    assert timestamp <= datetime.now()

def test_knowledge_base_integration():
    kb = WABusinessKnowledge()
    
    # Test minimum wage
    assert kb.get_minimum_wage("washington") >= 16.28
    assert kb.get_minimum_wage("seattle") >= 19.97
    
    # Test license requirements
    requirements = kb.get_license_requirements()
    assert len(requirements) > 0
    
    # Test fees
    fees = kb.get_fees()
    assert fees["new_business"] >= 90
    
    # Test static data
    assert len(kb.get_starting_steps()) > 0
    assert len(kb.get_essential_links()) > 0
    assert len(kb.get_payroll_taxes()) > 0
    assert len(kb.get_business_types()) > 0
    
    # Test employer requirements
    emp_reqs = kb.get_employer_requirements()
    assert "required_insurance" in emp_reqs
    assert "required_reporting" in emp_reqs
    assert "workplace_requirements" in emp_reqs

def test_knowledge_base_initialization():
    kb = WABusinessKnowledge()
    assert kb is not None

def test_starting_steps():
    kb = WABusinessKnowledge()
    steps = kb.get_starting_steps()
    assert isinstance(steps, list)
    assert len(steps) > 0
    assert all(isinstance(step, dict) for step in steps)
    assert all("step" in step for step in steps)
    assert all("description" in step for step in steps)
    assert all("key_points" in step for step in steps)
    assert all("links" in step for step in steps)

def test_essential_links():
    kb = WABusinessKnowledge()
    links = kb.get_essential_links()
    assert isinstance(links, dict)
    assert "business_license" in links
    assert "ubi_info" in links
    assert all(isinstance(url, str) for url in links.values())
    assert all(url.startswith("http") for url in links.values())

def test_faqs(scraper):
    """Test FAQ data retrieval."""
    faqs = scraper.get_faqs()
    assert isinstance(faqs, list)
    assert len(faqs) > 0
    
    # Test FAQ structure
    for faq in faqs:
        assert isinstance(faq, dict)
        assert 'question' in faq
        assert 'answer' in faq
        assert 'html_answer' in faq
        assert 'links' in faq
        assert 'category' in faq
        assert 'metadata' in faq
        
        # Test links structure
        for link in faq['links']:
            assert 'text' in link
            assert 'value' in link
            assert 'type' in link
            assert link['type'] in ['url', 'email']
            
            if link['type'] == 'url':
                assert link['value'].startswith('http')
            elif link['type'] == 'email':
                assert link['value'].startswith('mailto:')
        
        # Test metadata structure
        assert 'id' in faq['metadata']
        assert 'last_updated' in faq['metadata']

def test_faq_categorization(scraper):
    """Test FAQ categorization logic."""
    test_questions = {
        'Do I need business insurance?': 'insurance',
        'How do I form an LLC?': 'business_structure',
        'Do I need a business license?': 'licensing',
        'What taxes do I need to pay?': 'tax',
        'How do I hire employees?': 'employment',
        'Can I drive for Uber?': 'rideshare',
        'What is the weather like?': 'general'  # Default category
    }
    
    for question, expected_category in test_questions.items():
        assert scraper._categorize_faq(question) == expected_category 