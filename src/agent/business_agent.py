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
import json

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

    async def _analyze_query_with_llm(self, query: str) -> Dict[str, Any]:
        """Analyze the query using LLM to determine intent and business type."""
        # Force flow chart generation if the query contains 'flow chart' or 'flowchart'
        if 'flow chart' in query.lower() or 'flowchart' in query.lower():
            # Try to extract business type from the query
            business_types = {
                "hair salon": ["hair", "salon", "barber", "beauty"],
                "food truck": ["food", "truck", "cart", "vendor", "mobile"],
                "rideshare": ["rideshare", "uber", "lyft", "taxi", "driver"],
                "restaurant": ["restaurant", "cafe", "dining", "food service"],
                "retail": ["retail", "store", "shop", "boutique"],
                "online": ["online", "ecommerce", "web", "internet"],
                "construction": ["construction", "contractor", "building"],
                "consulting": ["consulting", "freelance", "professional service"]
            }
            
            for business_type, keywords in business_types.items():
                if any(keyword in query.lower() for keyword in keywords):
                    return {"needs_flow_chart": True, "business_type": business_type, "confidence": 1.0}
            
            # Check conversation history for business type if not found in current query
            if self.conversation_history:
                for msg in reversed(self.conversation_history):
                    if msg["role"] == "user":
                        for business_type, keywords in business_types.items():
                            if any(keyword in msg["content"].lower() for keyword in keywords):
                                return {"needs_flow_chart": True, "business_type": business_type, "confidence": 0.8}
            
            return {"needs_flow_chart": True, "business_type": None, "confidence": 1.0}
        
        system_prompt = """You are a business analysis assistant. Analyze the given query and determine:
1. If the user is requesting a flow chart or step-by-step process
2. What type of business they're interested in (if any)

The system CAN generate flow charts, so if the user asks for a flow chart, diagram, or steps, set needs_flow_chart to true.
Even if they don't explicitly mention a business type, if the context suggests they want business formation steps, set needs_flow_chart to true.

Respond in JSON format with the following structure:
{
    "needs_flow_chart": boolean,
    "business_type": string or null,
    "confidence": float (0-1)
}

Examples of flow chart requests:
- "Can you generate a flow chart for me?" -> needs_flow_chart: true
- "Show me the steps to start a business" -> needs_flow_chart: true
- "How do I start a restaurant?" -> needs_flow_chart: true, business_type: "restaurant"
- "What's the process for becoming an Uber driver?" -> needs_flow_chart: true, business_type: "rideshare"
- "I want a flow chart for a hair salon" -> needs_flow_chart: true, business_type: "hair salon"

If no specific business type is mentioned, set business_type to null.
If the query is ambiguous about needing a flow chart, set needs_flow_chart to false.
"""

        # Include conversation history in the messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history (up to 3 previous exchanges)
        history_to_include = self.conversation_history[-6:] if len(self.conversation_history) > 6 else self.conversation_history
        messages.extend(history_to_include)
        
        # Add the current query
        messages.append({"role": "user", "content": query})

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",  # or your specific model
                messages=messages,
                temperature=0.1,  # Low temperature for more consistent results
                response_format={ "type": "json_object" }
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            logger.error(f"Error in LLM query analysis: {str(e)}")
            return {"needs_flow_chart": False, "business_type": None, "confidence": 0.0}

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
                    "• Starting any type of business in Washington\n"
                    "• Business licensing and fees\n"
                    "• Minimum wage requirements\n"
                    "• Step-by-step guidance\n"
                    "• Flow charts for business formation\n\n"
                    "What would you like to know about?"
                )
                self.conversation_history.append({"role": "assistant", "content": greeting_response})
                return greeting_response

            # Analyze query using LLM
            analysis = await self._analyze_query_with_llm(query)
            
            if analysis["needs_flow_chart"]:
                business_type = analysis["business_type"]
                
                if not business_type:
                    # Ask user to specify business type
                    response = (
                        "I can create a flow chart showing the steps to form your business. "
                        "What type of business would you like to start? I can help with any type, including:\n"
                        "• Retail Store or Shop\n"
                        "• Restaurant or Food Service\n"
                        "• Rideshare or Transportation\n"
                        "• Online Business\n"
                        "• Construction or Contracting\n"
                        "• Personal Services (Salon, Spa, etc.)\n"
                        "• Consulting or Freelancing\n"
                        "• Or any other type of business"
                    )
                else:
                    # Generate flow chart
                    try:
                        flow_data = await self.generate_formation_flow(business_type)
                        
                        # Format the response with the flow chart data
                        response = (
                            f"I've created a flow chart showing the steps to start your {business_type.replace('_', ' ')} business. "
                            "The chart shows the required steps, their order, and any tasks that can be done in parallel.\n\n"
                            "<flow_chart_data>" + json.dumps(flow_data) + "</flow_chart_data>\n\n"
                            "Would you like me to explain any specific step in more detail?"
                        )
                        
                        # Log the flow chart data for debugging
                        logger.debug(f"Generated flow chart data: {json.dumps(flow_data)}")
                    except Exception as e:
                        logger.error(f"Error generating flow chart: {str(e)}")
                        response = (
                            f"I encountered an error while creating the flow chart. "
                            "Please try rephrasing your request or ask about a different business type."
                        )
                
                self.conversation_history.append({"role": "assistant", "content": response})
                return response

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
    
    async def generate_formation_flow(self, business_type: str) -> dict:
        """
        Dynamically generate a flow chart for business formation based on the agent's knowledge.
        """
        # Normalize business type
        business_type = business_type.lower().replace('_', ' ')
        
        # Get formation steps from knowledge base
        formation_steps = await self._get_formation_steps(business_type)
        
        # Generate nodes and edges
        nodes = [{"id": "start", "text": "Start", "style": "fill:#f9f"}]
        edges = []
        last_id = "start"
        
        # Add business structure node
        structure_id = "structure"
        nodes.append({
            "id": structure_id,
            "text": f"{business_type.title()} Structure",
            "style": "fill:#bbf"
        })
        edges.append([last_id, structure_id])
        last_id = structure_id
        
        # Process each formation step
        for idx, step in enumerate(formation_steps):
            step_id = f"step_{idx}"
            nodes.append({
                "id": step_id,
                "text": step["title"],
                "style": self._get_step_style(step["category"])
            })
            
            # Connect to previous node
            edges.append([last_id, step_id])
            
            # If there are parallel steps, create branches
            if "parallel_steps" in step:
                for p_idx, parallel_step in enumerate(step["parallel_steps"]):
                    p_id = f"parallel_{idx}_{p_idx}"
                    nodes.append({
                        "id": p_id,
                        "text": parallel_step["title"],
                        "style": self._get_step_style(parallel_step["category"])
                    })
                    edges.append([step_id, p_id])
            
            last_id = step_id
        
        return {"nodes": nodes, "edges": edges}
    
    async def _get_formation_steps(self, business_type: str) -> list:
        """
        Get the formation steps for a specific business type by querying the LLM.
        """
        try:
            # Enhanced fallback steps for rideshare businesses
            if "rideshare" in business_type.lower() or any(term in business_type.lower() for term in ["uber", "lyft", "taxi"]):
                return [
                    {"title": "Register as a Sole Proprietorship or LLC", "category": "legal"},
                    {"title": "Get UBI Number", "category": "administrative"},
                    {"title": "Federal EIN (Optional for Sole Proprietorship)", "category": "administrative"},
                    {"title": "Business License", "category": "legal"},
                    {
                        "title": "Vehicle Requirements",
                        "category": "compliance",
                        "parallel_steps": [
                            {"title": "Vehicle Registration and Insurance", "category": "compliance"},
                            {"title": "Vehicle Inspection", "category": "compliance"},
                            {"title": "For-Hire Vehicle Endorsement", "category": "legal"}
                        ]
                    },
                    {
                        "title": "Driver Requirements",
                        "category": "compliance",
                        "parallel_steps": [
                            {"title": "For-Hire Driver's License", "category": "legal"},
                            {"title": "Background Check", "category": "compliance"},
                            {"title": "Medical Examination", "category": "compliance"}
                        ]
                    },
                    {
                        "title": "Platform Setup",
                        "category": "administrative",
                        "parallel_steps": [
                            {"title": "Sign up with Uber/Lyft", "category": "administrative"},
                            {"title": "Complete Platform Training", "category": "administrative"},
                            {"title": "Set Up Payment Processing", "category": "financial"}
                        ]
                    },
                    {"title": "Business Insurance", "category": "compliance"},
                    {"title": "Tax Registration", "category": "financial"}
                ]
            
            # Enhanced fallback steps for food truck businesses
            if "food" in business_type.lower() and any(term in business_type.lower() for term in ["truck", "cart", "vendor", "mobile"]):
                return [
                    {"title": "Choose Business Structure", "category": "legal"},
                    {"title": "Register Business Name", "category": "administrative"},
                    {"title": "Get UBI Number", "category": "administrative"},
                    {"title": "Federal EIN", "category": "administrative"},
                    {"title": "Business License", "category": "legal"},
                    {
                        "title": "Food Service Permits",
                        "category": "compliance",
                        "parallel_steps": [
                            {"title": "Food Worker Card", "category": "compliance"},
                            {"title": "Mobile Food Unit Permit", "category": "compliance"},
                            {"title": "Health Department Inspection", "category": "compliance"}
                        ]
                    },
                    {
                        "title": "Vehicle Requirements",
                        "category": "compliance",
                        "parallel_steps": [
                            {"title": "Vehicle Registration", "category": "administrative"},
                            {"title": "Vehicle Inspection", "category": "compliance"},
                            {"title": "Equipment Installation", "category": "compliance"}
                        ]
                    },
                    {"title": "Location Permits", "category": "compliance"},
                    {"title": "Business Insurance", "category": "compliance"},
                    {"title": "Sales Tax Registration", "category": "financial"}
                ]
            
            # Enhanced fallback steps for hair salon businesses
            if "hair" in business_type.lower() or "salon" in business_type.lower() or "barber" in business_type.lower() or "beauty" in business_type.lower():
                return [
                    {"title": "Choose Business Structure", "category": "legal"},
                    {"title": "Register Business Name", "category": "administrative"},
                    {"title": "Get UBI Number", "category": "administrative"},
                    {"title": "Federal EIN", "category": "administrative"},
                    {"title": "Business License", "category": "legal"},
                    {
                        "title": "Cosmetology Licenses",
                        "category": "compliance",
                        "parallel_steps": [
                            {"title": "Cosmetology License", "category": "compliance"},
                            {"title": "Barber License (if applicable)", "category": "compliance"},
                            {"title": "Esthetician License (if applicable)", "category": "compliance"}
                        ]
                    },
                    {
                        "title": "Location Setup",
                        "category": "compliance",
                        "parallel_steps": [
                            {"title": "Find Suitable Location", "category": "administrative"},
                            {"title": "Sign Lease Agreement", "category": "legal"},
                            {"title": "Obtain Zoning Permits", "category": "compliance"}
                        ]
                    },
                    {
                        "title": "Health & Safety Requirements",
                        "category": "compliance",
                        "parallel_steps": [
                            {"title": "Health Department Inspection", "category": "compliance"},
                            {"title": "Fire Safety Inspection", "category": "compliance"},
                            {"title": "Set Up Sanitation Stations", "category": "compliance"}
                        ]
                    },
                    {"title": "Equipment & Supplies", "category": "administrative"},
                    {"title": "Business Insurance", "category": "compliance"},
                    {"title": "Sales Tax Registration", "category": "financial"},
                    {"title": "Marketing & Advertising", "category": "administrative"}
                ]
            
            # Get formation steps from knowledge base
            formation_steps = await self._get_formation_steps_from_knowledge(business_type)
            
            # If no steps were found, use generic steps
            if not formation_steps:
                return [
                    {"title": "Choose Business Structure", "category": "legal"},
                    {"title": "Register Business Name", "category": "administrative"},
                    {"title": "Get UBI Number", "category": "administrative"},
                    {"title": "Federal EIN", "category": "administrative"},
                    {"title": "Business License", "category": "legal"},
                    {"title": "Industry Permits", "category": "compliance"},
                    {"title": "Business Insurance", "category": "compliance"},
                    {"title": "Sales Tax Registration", "category": "financial"}
                ]
            
            return formation_steps
        except Exception as e:
            logger.error(f"Error getting formation steps: {str(e)}")
            # Return generic steps as fallback
            return [
                {"title": "Choose Business Structure", "category": "legal"},
                {"title": "Register Business Name", "category": "administrative"},
                {"title": "Get UBI Number", "category": "administrative"},
                {"title": "Federal EIN", "category": "administrative"},
                {"title": "Business License", "category": "legal"},
                {"title": "Industry Permits", "category": "compliance"},
                {"title": "Business Insurance", "category": "compliance"},
                {"title": "Sales Tax Registration", "category": "financial"}
            ]
    
    def _get_step_style(self, category: str) -> str:
        """
        Get the style for a step based on its category.
        """
        styles = {
            "legal": "fill:#ddf",
            "financial": "fill:#ffe",
            "administrative": "fill:#ddf",
            "compliance": "fill:#bfb"
        }
        return styles.get(category.lower(), "fill:#ddf")

    async def _get_llm_response(self, prompt: str) -> str:
        """
        Get a response from the LLM model.
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a Washington State business expert. "
                        "Provide accurate, structured information about business formation steps. "
                        "Format responses as Python data structures when requested."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.1,  # Low temperature for more structured output
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error getting LLM response: {str(e)}")
            raise 