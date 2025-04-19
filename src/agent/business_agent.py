from typing import Dict, List, Any, Optional
from src.knowledge_base.static_knowledge import WABusinessKnowledge
from src.config.config import settings
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import re
import aiohttp
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class BusinessAgent:
    def __init__(self):
        self.knowledge = WABusinessKnowledge()
        
        # Initialize AsyncOpenAI client with Azure endpoint
        load_dotenv()
        self.client = AsyncOpenAI(
            api_key=os.environ.get("GITHUB_TOKEN"),
            base_url="https://models.inference.ai.azure.com/"
        )
        
        # Initialize conversation state
        self.conversation_history = []
        self.max_history = 5  # Keep last 5 exchanges for context
        
        # Official URLs for real-time information
        self.official_urls = {
            'minimum_wage': 'https://lni.wa.gov/workers-rights/wages/minimum-wage/',
            'local_wages': 'https://lni.wa.gov/workers-rights/wages/minimum-wage/local-minimum-wage-rates',
            'business_license': 'https://dor.wa.gov/open-business/apply-business-license',
            'small_business_guide': 'https://www.business.wa.gov/site/alias__business/878/Small-Business-Guide.aspx',
            'business_structures': 'https://www.sos.wa.gov/corps/limited-liability-companies-limited-partnerships-and-limited-liability-partnerships.aspx'
        }
    
    def _is_greeting(self, text: str) -> bool:
        """Check if the input is a greeting."""
        greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        return any(text.lower().strip().startswith(greeting) for greeting in greetings)
    
    def _is_business_query(self, text: str) -> bool:
        """Check if the query is business-related."""
        business_keywords = [
            'business', 'license', 'permit', 'fee', 'tax', 'register', 'start',
            'open', 'company', 'llc', 'corporation', 'wage', 'employee', 'cost'
        ]
        return any(keyword in text.lower() for keyword in business_keywords)
    
    def _get_relevant_info(self, query: str) -> Dict[str, Any]:
        """Get only the relevant information based on the query."""
        info = {}
        query_lower = query.lower()
        
        # Only include license requirements if specifically asked about licenses or requirements
        if any(word in query_lower for word in ['license', 'permit', 'require', 'need to do']):
            info['requirements'] = "\n".join(self.knowledge.get_license_requirements())
        
        # Only include fees if asked about costs or fees
        if any(word in query_lower for word in ['fee', 'cost', 'pay', 'price', 'charge']):
            info['fees'] = str(self.knowledge.get_fees())
        
        # Only include steps if asked about process or steps
        if any(word in query_lower for word in ['step', 'process', 'start', 'begin', 'how to', 'guide']):
            info['steps'] = str(self.knowledge.get_starting_steps())
        
        # Include minimum wage info if asked about wages
        if any(word in query_lower for word in ['wage', 'salary', 'pay rate', 'minimum']):
            info['minimum_wage'] = str(self.knowledge.get_minimum_wage(None))
        
        return info

    async def _fetch_url_content(self, url: str) -> str:
        """Fetch content from a URL asynchronously."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Get text and clean it up
                        text = soup.get_text(separator=' ', strip=True)
                        # Remove extra whitespace and normalize
                        text = ' '.join(text.split())
                        return text
                    else:
                        logger.warning(f"Failed to fetch content from {url}, status: {response.status}")
                        return ""
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {str(e)}")
            return ""
    
    async def _get_relevant_content(self, query: str) -> Dict[str, str]:
        """Get relevant content from official sources based on the query."""
        content = {}
        query_lower = query.lower()
        
        # Define keyword mappings for URLs
        url_keywords = {
            'minimum_wage': ['wage', 'salary', 'pay', 'minimum'],
            'local_wages': ['seattle', 'local', 'city', 'county', 'regional'],
            'business_license': ['license', 'permit', 'registration', 'ubi'],
            'small_business_guide': ['guide', 'start', 'help', 'how to', 'steps'],
            'business_structures': ['llc', 'corporation', 'structure', 'partnership']
        }
        
        # Fetch content from relevant URLs based on keywords
        for url_key, keywords in url_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                url = self.official_urls.get(url_key)
                if url:
                    content[url_key] = await self._fetch_url_content(url)
        
        return content

    async def get_business_advice(self, query: str) -> str:
        try:
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": query})
            if len(self.conversation_history) > self.max_history * 2:
                self.conversation_history = self.conversation_history[-self.max_history * 2:]
            
            # Handle greetings
            if self._is_greeting(query) and not self._is_business_query(query):
                greeting_response = (
                    "Hello! I'm your Washington State business assistant. "
                    "I can help you with information about:\n"
                    "• Starting a business in Washington\n"
                    "• Business licensing and fees\n"
                    "• Minimum wage requirements\n"
                    "• Step-by-step guidance\n\n"
                    "What would you like to know about?"
                )
                self.conversation_history.append({"role": "assistant", "content": greeting_response})
                return greeting_response
            
            # Get real-time content from relevant URLs
            relevant_content = await self._get_relevant_content(query)
            
            # Construct the system message
            system_message = {
                "role": "system",
                "content": (
                    "You are a Washington State business advisor. "
                    "Provide specific, actionable advice based on official WA state regulations. "
                    "Be conversational and friendly, but professional. "
                    "Only include information that is relevant to the user's question. "
                    "When citing information, mention the official source. "
                    "If you're not sure about something, say so and suggest where they might find that information."
                )
            }
            
            # Construct the user message with relevant context
            context_str = ""
            if relevant_content:
                context_str = "\nHere's the latest information from official Washington State sources:\n"
                for source, content in relevant_content.items():
                    if content:  # Only include non-empty content
                        context_str += f"\nFrom {self.official_urls[source]}:\n{content[:1000]}..."  # Limit content length
            
            messages = [
                system_message,
                *self.conversation_history[:-1],
                {
                    "role": "user",
                    "content": f"{query}\n\n{context_str if context_str else ''}"
                }
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            assistant_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            return assistant_response
            
        except Exception as e:
            error_msg = (
                "I apologize, but I encountered an error while processing your request. "
                "Please try asking your question again, or you can visit the official "
                "Washington State Business website for immediate assistance."
            )
            logger.error(f"Error in get_business_advice: {str(e)}")
            self.conversation_history.append({"role": "assistant", "content": error_msg})
            return error_msg
    
    async def suggest_documents(self, business_context: Dict[str, Any]) -> str:
        try:
            available_docs = str(self.knowledge.get_essential_links())
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a Washington State business advisor. Help users find and understand required documents and forms."
                },
                {
                    "role": "user",
                    "content": f"""
                    Based on the business context provided:
                    {business_context}
                    
                    Suggest relevant documents and forms needed from these categories:
                    {available_docs}
                    
                    For each document:
                    1. Explain why it's needed
                    2. Provide the official link
                    3. List any prerequisites
                    4. Mention associated fees
                    """
                }
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using Azure's model
                messages=messages,
                temperature=0.1,
                max_tokens=800
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error suggesting documents: {str(e)}")
    
    def get_minimum_wage(self, location: str) -> float:
        return self.knowledge.get_minimum_wage(location)
    
    def get_starting_steps(self) -> List[Dict[str, Any]]:
        return self.knowledge.get_starting_steps()
    
    def get_essential_links(self) -> Dict[str, str]:
        return self.knowledge.get_essential_links() 