import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from cachetools import TTLCache
import logging
import re
from ..database.db import Database

logger = logging.getLogger(__name__)

class WABusinessScraper:
    """Scraper for Washington State business information."""
    
    def __init__(self, db: Optional[Database] = None):
        self.base_url = "https://www.business.wa.gov"
        self.cache = TTLCache(maxsize=100, ttl=3600)  # Cache for 1 hour
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WA Business Agent/1.0 (Educational Purpose)'
        })
        self.db = db or Database()

    def _get_cached_or_fetch(self, key: str, fetch_func) -> Any:
        """Get data from cache or fetch it using the provided function."""
        if key not in self.cache:
            try:
                self.cache[key] = fetch_func()
            except Exception as e:
                logger.error(f"Error fetching {key}: {str(e)}")
                if key == 'minimum_wage':
                    return self._get_default_minimum_wage()
                elif key == 'license_requirements':
                    return self._get_default_license_requirements()
                elif key == 'fees':
                    return self._get_default_fees()
                elif key == 'faqs':
                    return self._get_default_faqs()
                raise
        return self.cache[key]

    def _fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse a webpage."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'lxml')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise

    def get_minimum_wage(self) -> Dict[str, float]:
        """Fetch current minimum wage information from L&I website."""
        def fetch():
            try:
                wage_data = {}
                
                # Get state minimum wage from main page
                state_soup = self._fetch_page("https://lni.wa.gov/workers-rights/wages/minimum-wage/")
                state_wage_section = state_soup.find(lambda tag: tag.name and "The 2025 Minimum Wage" in tag.text)
                if state_wage_section:
                    state_wage_match = re.search(r'\$(\d+\.\d+)', state_wage_section.text)
                    if state_wage_match:
                        wage_data["washington"] = float(state_wage_match.group(1))
                
                # Get local minimum wages
                local_soup = self._fetch_page("https://lni.wa.gov/workers-rights/wages/minimum-wage/local-minimum-wage-rates")
                
                # Define city patterns with their variations
                city_patterns = {
                    'seattle': r'Seattle:\s*\$(\d+\.\d+)',
                    'seatac': r'SeaTac:\s*\$(\d+\.\d+)',
                    'tukwila': r'Tukwila:\s*\$(\d+\.\d+).*?(?:employers with 500 or more employees)',
                    'burien': r'Burien:\s*\$(\d+\.\d+).*?(?:employers with more than 500 employees)',
                    'bellingham': r'Bellingham:\s*\$(\d+\.\d+)',
                    'everett': r'Everett:.*?\$(\d+\.\d+).*?(?:employers with more than 500 employees)',
                    'king_county': r'King County.*?\$(\d+\.\d+).*?(?:employers with more than 500)',
                    'renton': r'Renton:\s*\$(\d+\.\d+).*?(?:employers with 501 or more employees)'
                }
                
                content = local_soup.get_text()
                
                # Extract wages for each city
                for city, pattern in city_patterns.items():
                    match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                    if match:
                        wage_data[city] = float(match.group(1))
                
                if not wage_data:
                    logger.warning("No minimum wage data found, using defaults")
                    return self._get_default_minimum_wage()
                
                return wage_data
            except Exception as e:
                logger.error(f"Error parsing minimum wage data: {str(e)}")
                return self._get_default_minimum_wage()

        return self._get_cached_or_fetch('minimum_wage', fetch)

    def get_license_requirements(self) -> List[str]:
        """Fetch business license requirements."""
        def fetch():
            try:
                soup = self._fetch_page(f"{self.base_url}/site/alias__business/875/Home.aspx")
                requirements = []
                
                # Find the license requirements section
                license_section = soup.find(lambda tag: tag.name and "Who needs a business license" in tag.text)
                if license_section:
                    # Extract bullet points or list items
                    requirements = [
                        item.text.strip()
                        for item in license_section.find_all(['li', 'p'])
                        if item.text.strip() and not item.find('a')  # Exclude navigation links
                    ]

                return requirements or self._get_default_license_requirements()
            except Exception as e:
                logger.error(f"Error parsing license requirements: {str(e)}")
                return self._get_default_license_requirements()

        return self._get_cached_or_fetch('license_requirements', fetch)

    def get_fees(self) -> Dict[str, float]:
        """Fetch current fee structure."""
        def fetch():
            try:
                soup = self._fetch_page(f"{self.base_url}/site/alias__business/875/Home.aspx")
                fees = {}
                
                # Find the fees section
                fees_section = soup.find(lambda tag: tag.name and "business license application" in tag.text.lower())
                if fees_section:
                    # Extract fee amounts
                    fee_matches = re.finditer(r'\$(\d+)', fees_section.text)
                    for match in fee_matches:
                        amount = float(match.group(1))
                        if amount == 90:
                            fees["new_business"] = amount
                        elif amount == 19:
                            fees["additional"] = amount

                return fees or self._get_default_fees()
            except Exception as e:
                logger.error(f"Error parsing fees: {str(e)}")
                return self._get_default_fees()

        return self._get_cached_or_fetch('fees', fetch)

    def get_faqs(self) -> List[Dict[str, Any]]:
        """Fetch and parse FAQ information from the website."""
        def fetch():
            try:
                soup = self._fetch_page(f"{self.base_url}/site/alias__business/875/Home.aspx")
                faqs = []
                
                # Try different selectors for FAQ section
                faq_section = (
                    soup.find('section', class_='faq-section') or
                    soup.find('div', class_='faq-section') or
                    soup.find('div', class_='faqs') or
                    soup.find('section', class_='faqs') or
                    soup.find(lambda tag: tag.name and any(text in tag.text.lower() 
                        for text in ['frequently asked questions', 'faqs', 'common questions']))
                )
                
                if faq_section:
                    logger.info("Found FAQ section")
                    # Try different selectors for FAQ items
                    cards = (
                        faq_section.find_all('div', class_='card') or
                        faq_section.find_all('div', class_='faq-item') or
                        faq_section.find_all('div', class_='accordion-item') or
                        faq_section.find_all(['div', 'section'], class_=lambda x: x and any(c in x.lower() for c in ['faq', 'question']))
                    )
                    
                    logger.info(f"Found {len(cards)} FAQ items")
                    
                    for card in cards:
                        # Try different selectors for question
                        question = (
                            card.find('span', class_='question') or
                            card.find('div', class_='question') or
                            card.find(['h2', 'h3', 'h4', 'strong', 'span'], class_=lambda x: x and 'question' in x.lower() if x else False) or
                            card.find(['h2', 'h3', 'h4', 'strong', 'span'])
                        )
                        
                        # Try different selectors for answer
                        answer = (
                            card.find('div', class_='card-body') or
                            card.find('div', class_='answer') or
                            card.find('div', class_='content') or
                            card.find(['div', 'p'], class_=lambda x: x and 'answer' in x.lower() if x else False)
                        )
                        
                        if question and answer:
                            links = []
                            for a in answer.find_all('a'):
                                href = a.get('href', '')
                                if href.startswith('mailto:'):
                                    link_type = 'email'
                                    value = href
                                else:
                                    link_type = 'url'
                                    value = self._normalize_url(href)
                                
                                links.append({
                                    'text': a.text.strip(),
                                    'value': value,
                                    'type': link_type
                                })

                            faq = {
                                'question': question.text.strip(),
                                'answer': answer.text.strip(),
                                'links': links,
                                'metadata': {
                                    'id': card.get('id', '') or question.get('id', '') or f"faq_{len(faqs) + 1}"
                                }
                            }
                            faqs.append(faq)
                            logger.info(f"Added FAQ: {faq['question'][:50]}...")
                else:
                    logger.warning("Could not find FAQ section")
                
                if not faqs:
                    logger.warning("No FAQs found, using defaults")
                    return self._get_default_faqs()
                    
                return faqs
            except Exception as e:
                logger.error(f"Error parsing FAQs: {str(e)}")
                return self._get_default_faqs()

        return self._get_cached_or_fetch('faqs', fetch)

    def get_stored_faqs(self) -> List[Dict[str, Any]]:
        """Retrieve all FAQs from the database."""
        return self.db.get_all_faqs()

    def get_stored_faqs_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Retrieve FAQs by category from the database."""
        return self.db.get_faqs_by_category(category)

    def _normalize_url(self, url: str) -> str:
        """Convert relative URLs to absolute URLs."""
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return f"{self.base_url}{url}"
        else:
            return f"{self.base_url}/{url}"

    def _get_default_minimum_wage(self) -> Dict[str, float]:
        """Default minimum wage data."""
        return {
            "washington": 16.66,  # 2025 state minimum wage
            "seattle": 20.76,
            "seatac": 20.17,
            "tukwila": 21.10,
            "burien": 21.16,
            "bellingham": 17.66,
            "everett": 20.24,
            "king_county": 20.29,
            "renton": 20.90
        }

    def _get_default_license_requirements(self) -> List[str]:
        """Default license requirements."""
        return [
            "Business requires city/state endorsements",
            "Using business name different from legal name",
            "Planning to hire employees within 90 days",
            "Collecting sales tax",
            "Gross income ≥ $12,000 per year",
            "Required to pay taxes/fees to Department of Revenue",
            "Buyer/processor of specialty wood products"
        ]

    def _get_default_fees(self) -> Dict[str, float]:
        """Default fees."""
        return {
            "new_business": 90,  # Opening first location or reopening a business
            "additional": 19     # Additional endorsements, trade names, etc.
        }

    def _get_default_faqs(self) -> List[Dict[str, Any]]:
        """Return default FAQs in case scraping fails."""
        return [
            {
                "question": "What licenses do I need to start a business in Washington?",
                "category": "licensing",
                "links": [
                    {
                        "text": "Business Licensing",
                        "value": "https://dor.wa.gov/open-business/apply-business-license",
                        "type": "external"
                    }
                ]
            },
            {
                "question": "What is the current minimum wage in Washington State?",
                "category": "compliance",
                "links": [
                    {
                        "text": "Minimum Wage Requirements",
                        "value": "https://www.lni.wa.gov/workers-rights/wages/minimum-wage/",
                        "type": "external"
                    }
                ]
            },
            {
                "question": "How do I register my business for taxes in Washington?",
                "category": "taxes",
                "links": [
                    {
                        "text": "Business Tax Registration",
                        "value": "https://dor.wa.gov/taxes-rates",
                        "type": "external"
                    }
                ]
            },
            {
                "question": "What business structure should I choose?",
                "category": "planning",
                "links": [
                    {
                        "text": "Business Structures Guide",
                        "value": "https://www.sos.wa.gov/corps/limited-liability-companies-limited-partnerships-and-limited-liability-partnerships.aspx",
                        "type": "external"
                    }
                ]
            },
            {
                "question": "Do I need workers' compensation insurance?",
                "category": "insurance",
                "links": [
                    {
                        "text": "Workers' Compensation Information",
                        "value": "https://www.lni.wa.gov/insurance/insurance-requirements/",
                        "type": "external"
                    }
                ]
            }
        ]

    def clear_cache(self) -> None:
        """Clear the cache to force fresh data fetch."""
        self.cache.clear()

    def get_last_updated(self) -> datetime:
        """Get the timestamp of the last data update."""
        return datetime.now() - timedelta(seconds=self.cache.ttl)

    def close(self):
        """Close database connection."""
        self.db.close()

    def get_resource_links(self) -> List[Dict[str, Any]]:
        """Fetch and parse business resource links from the website."""
        def fetch():
            try:
                soup = self._fetch_page(f"{self.base_url}/site/alias__business/875/Home.aspx")
                resources = []
                
                # Find the resources section
                resources_section = soup.find(lambda tag: tag.name == 'section' and 
                    tag.find('h3', text=lambda t: t and 'Linking you to more resources' in t))
                
                if resources_section:
                    # Find all link boxes
                    link_boxes = resources_section.find_all('div', class_='link-txt-box')
                    
                    for box in link_boxes:
                        title = box.find('h6')
                        link = box.find('a')
                        
                        if title and link:
                            href = link.get('href', '')
                            resource = {
                                'title': title.text.strip(),
                                'url': self._normalize_url(href),
                                'aria_label': link.get('aria-label', ''),
                                'category': self._categorize_resource(title.text.strip(), href)
                            }
                            resources.append(resource)
                            
                            # Save to database
                            try:
                                self.db.save_resource_link(resource)
                            except Exception as e:
                                logger.error(f"Error saving resource link to database: {str(e)}")

                result = resources or self._get_default_resource_links()
                
                # Export to CSV
                try:
                    self.db.export_resource_links_to_csv()
                except Exception as e:
                    logger.error(f"Error exporting resource links to CSV: {str(e)}")
                
                return result
            except Exception as e:
                logger.error(f"Error parsing resource links: {str(e)}")
                return self._get_default_resource_links()

        return self._get_cached_or_fetch('resource_links', fetch)

    def get_stored_resource_links(self) -> List[Dict[str, Any]]:
        """Retrieve all resource links from the database."""
        return self.db.get_all_resource_links()

    def get_stored_resource_links_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Retrieve resource links by category from the database."""
        return self.db.get_resource_links_by_category(category)

    def _categorize_resource(self, title: str, url: str) -> str:
        """Categorize resource links based on their titles and URLs."""
        title_lower = title.lower()
        url_lower = url.lower()
        
        # Combined text for searching
        search_text = f"{title_lower} {url_lower}"
        
        # Licensing category
        if any(word in search_text for word in [
            'license', 'permit', 'registration', 'business service', 'endorsement',
            'certification', 'regulatory', 'compliance', 'filing', 'register',
            'dor.wa.gov', 'ubi', 'tax', 'revenue'
        ]):
            return 'licensing'
        
        # Planning category
        elif any(word in search_text for word in [
            'plan', 'start', 'opening', 'checklist', 'strategy', 'roadmap',
            'preparation', 'setup', 'establish', 'launch', 'assessment',
            'business-plan', 'startup', 'planning', 'market-research'
        ]):
            return 'planning'
        
        # Tools category
        elif any(word in search_text for word in [
            'calculator', 'payroll', 'assistance tools', 'wizard', 'estimator',
            'forms', 'templates', 'software', 'portal', 'system', 'finder',
            'tool', 'app', 'application', 'secure.dor', 'bls.dor'
        ]):
            return 'tools'
        
        # Guidance category
        elif any(word in search_text for word in [
            'guide', 'liaison', 'questions', 'research', 'contact', 'help',
            'support', 'assistance', 'resources', 'information', 'faq', 'learn',
            'education', 'training', 'mentor', 'consult', 'handbook', 'manual',
            'small-business-guide', 'help.business', 'sbdc', 'score'
        ]):
            return 'guidance'
        
        # Default category
        return 'other'

    def _get_default_resource_links(self) -> List[Dict[str, Any]]:
        """Return default resource links when scraping fails."""
        return [
            {
                'title': 'Business License Wizard',
                'url': 'https://secure.dor.wa.gov/gteunauth/?Link=wiz',
                'aria_label': 'Business License Wizard',
                'category': 'licensing'
            },
            {
                'title': 'Small Business Guide',
                'url': f"{self.base_url}/site/alias__business/875/Home.aspx#anchor-3574",
                'aria_label': 'Small Business Guide',
                'category': 'guidance'
            },
            {
                'title': 'Starting a Business',
                'url': f"{self.base_url}/site/alias__business/876/Small-Business-Guide--Start.aspx",
                'aria_label': 'Starting a Business',
                'category': 'planning'
            }
        ]

    def _process_resource_link(self, link_element: Any) -> Dict[str, Any]:
        """Process a resource link element and extract metadata."""
        try:
            url = link_element.get('href', '')
            title = link_element.text.strip()
            aria_label = link_element.get('aria-label', '')
            
            # Extract additional metadata
            metadata = {
                'type': 'external',
                'language': 'en',  # Default to English
                'format': self._determine_resource_format(url),
                'last_accessed': datetime.now().isoformat(),
                'requires_auth': False,  # Default assumption
                'is_government': '.gov' in url.lower(),
                'description': aria_label if aria_label else title,
            }
            
            # Determine if it's a document download
            if any(ext in url.lower() for ext in ['.pdf', '.doc', '.docx', '.xlsx', '.zip']):
                metadata['is_download'] = True
                metadata['file_type'] = url.split('.')[-1].lower()
            else:
                metadata['is_download'] = False
            
            return {
                'title': title,
                'url': url,
                'aria_label': aria_label,
                'category': self._categorize_resource(title, url),
                'metadata': metadata
            }
        except Exception as e:
            logging.error(f"Error processing resource link: {str(e)}")
            return None
            
    def _determine_resource_format(self, url: str) -> str:
        """Determine the format of a resource based on its URL."""
        url_lower = url.lower()
        if '.pdf' in url_lower:
            return 'PDF'
        elif any(ext in url_lower for ext in ['.doc', '.docx']):
            return 'Word Document'
        elif any(ext in url_lower for ext in ['.xls', '.xlsx']):
            return 'Excel Spreadsheet'
        elif '.zip' in url_lower:
            return 'ZIP Archive'
        elif any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif']):
            return 'Image'
        else:
            return 'Web Page' 