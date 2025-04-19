from typing import Dict, List, Optional, Union
from datetime import datetime
from .wa_scraper import WABusinessScraper

class WABusinessKnowledge:
    def __init__(self):
        self._scraper = WABusinessScraper()
        self._minimum_wage_data = {
            "washington": 16.28,
            "seattle": 19.97,
            "seatac": 19.71,
            "tukwila": 20.29
        }
        
        self._license_requirements = [
            "Business requires city/state endorsements",
            "Using business name different from legal name",
            "Planning to hire employees within 90 days",
            "Collecting sales tax",
            "Gross income ≥ $12,000 per year",
            "Required to pay taxes/fees to Department of Revenue",
            "Buyer/processor of specialty wood products"
        ]
        
        self._fees = {
            "new_business": 90.0,      # Opening first location or reopening a business
            "additional_purposes": 19.0  # Additional endorsements, locations, etc.
        }
        
        self._starting_steps = [
            {
                "step": "Plan Your Business",
                "description": "Develop your business plan and strategy",
                "key_points": ["Market research", "Financial projections", "Business model"],
                "links": ["https://business.wa.gov/plan"]
            },
            {
                "step": "Choose Business Structure",
                "description": "Select and register your business structure",
                "key_points": ["LLC", "Corporation", "Sole Proprietorship"],
                "links": ["https://sos.wa.gov/corps"]
            },
            {
                "step": "Get Licensed",
                "description": "Obtain necessary licenses and permits",
                "key_points": ["Business License", "UBI Number", "Endorsements"],
                "links": ["https://dor.wa.gov/licenses"]
            }
        ]
        
        self._essential_links = {
            "business_license": "https://dor.wa.gov/open-business/apply-business-license",
            "secretary_of_state": "https://www.sos.wa.gov/corps/",
            "labor_industries": "https://lni.wa.gov/",
            "employment_security": "https://esd.wa.gov/",
            "paid_family_leave": "https://paidleave.wa.gov",
            "small_business_guide": "https://www.business.wa.gov/site/alias__business/878/Small-Business-Guide.aspx",
            "ubi_info": "https://dor.wa.gov/taxes-rates/business-registration/ubi-number"
        }

    def get_minimum_wage(self, location: str = "washington") -> float:
        """Get the minimum wage for a specific location in Washington."""
        try:
            wage_data = self._scraper.get_minimum_wage()
            return wage_data.get(location.lower(), wage_data["washington"])
        except Exception:
            return self._minimum_wage_data.get(location.lower(), self._minimum_wage_data["washington"])

    def get_license_requirements(self) -> List[str]:
        """Get the list of conditions that require a business license."""
        try:
            return self._scraper.get_license_requirements()
        except Exception:
            return self._license_requirements

    def get_fees(self) -> Dict[str, float]:
        """Get the current fee structure for business licenses and related services."""
        try:
            scraped_fees = self._scraper.get_fees()
            # Ensure compatibility with both new and old key names
            if "new_business" in scraped_fees:
                self._fees["new_business"] = scraped_fees["new_business"]
            if "additional" in scraped_fees:
                self._fees["additional_purposes"] = scraped_fees["additional"]
            return self._fees
        except Exception:
            return self._fees

    def get_starting_steps(self) -> List[dict]:
        """Get the recommended steps for starting a business in Washington."""
        return self._starting_steps

    def get_essential_links(self) -> Dict[str, str]:
        """Get important links to government resources."""
        return self._essential_links

    def get_payroll_taxes(self) -> List[str]:
        """Get information about required payroll taxes."""
        return [
            "Workers' Compensation (L&I)",
            "Unemployment Insurance (ESD)",
            "Paid Family Medical Leave (ESD)"
        ]

    def get_business_types(self) -> List[str]:
        """Get available business structure types."""
        return [
            "Sole Proprietorship",
            "Limited Liability Company (LLC)",
            "Corporation",
            "Partnership",
            "Limited Partnership",
            "Nonprofit Corporation"
        ]

    def get_employer_requirements(self) -> Dict[str, List[str]]:
        """Get key employer requirements and responsibilities."""
        return {
            "required_insurance": [
                "Workers' Compensation Insurance",
                "Unemployment Insurance"
            ],
            "required_reporting": [
                "Quarterly tax reports",
                "New hire reporting",
                "Paid Family and Medical Leave premium payments"
            ],
            "workplace_requirements": [
                "Post required workplace posters",
                "Maintain employee records",
                "Follow minimum wage laws",
                "Follow overtime pay rules",
                "Provide paid sick leave"
            ]
        }
        
    def refresh_data(self) -> None:
        """Force a refresh of all scraped data."""
        self._scraper.clear_cache()
        
    def get_last_updated(self) -> datetime:
        """Get when the data was last updated."""
        return self._scraper.get_last_updated() 