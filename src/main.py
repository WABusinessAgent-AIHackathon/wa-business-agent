import sys
import os

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.knowledge_base.static_knowledge import WABusinessKnowledge
from src.agent.business_agent import BusinessAgent
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="WA Business Agent", debug=True)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Ensure directories exist with absolute paths
static_dir = os.path.join(PROJECT_ROOT, "static")
templates_dir = os.path.join(PROJECT_ROOT, "templates")

logger.debug(f"Project root: {PROJECT_ROOT}")
logger.debug(f"Static directory: {static_dir}")
logger.debug(f"Templates directory: {templates_dir}")

# Create directories if they don't exist
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates = Jinja2Templates(directory=templates_dir)

# Initialize knowledge base and agent
try:
    kb = WABusinessKnowledge()
    agent = BusinessAgent()
    logger.info("Successfully initialized knowledge base and agent")
except Exception as e:
    logger.error(f"Error initializing knowledge base or agent: {str(e)}")
    raise

class ChatMessage(BaseModel):
    text: str

class ChatResponse(BaseModel):
    text: str
    data: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, str]]] = None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        logger.debug("Rendering home template")
        return templates.TemplateResponse(
            "index.html",
            {"request": request}
        )
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(message: ChatMessage):
    try:
        logger.info(f"Processing chat message: {message.text}")
        response = await agent.get_business_advice(message.text)
        
        actions = [
            {"text": "Check business fees", "action": "fees"},
            {"text": "Get started", "action": "steps"}
        ]
        
        return ChatResponse(
            text=response,
            actions=actions
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fees")
async def get_fees():
    try:
        logger.info("Fetching fees")
        fees = kb.get_fees()
        logger.debug(f"Retrieved fees: {fees}")
        return fees
    except Exception as e:
        logger.error(f"Error getting fees: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/minimum-wage/{location}")
async def get_minimum_wage(location: str = None):
    try:
        logger.info(f"Fetching minimum wage for location: {location}")
        wage = kb.get_minimum_wage(location)
        logger.debug(f"Retrieved minimum wage: {wage}")
        return {"minimum_wage": wage}
    except Exception as e:
        logger.error(f"Error getting minimum wage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/starting-steps")
async def get_starting_steps():
    try:
        logger.info("Fetching starting steps")
        steps = kb.get_starting_steps()
        logger.debug(f"Retrieved steps: {steps}")
        return {"steps": steps}
    except Exception as e:
        logger.error(f"Error getting starting steps: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/essential-links")
async def get_essential_links():
    try:
        logger.info("Fetching essential links")
        links = kb.get_essential_links()
        logger.debug(f"Retrieved links: {links}")
        return {"links": links}
    except Exception as e:
        logger.error(f"Error getting essential links: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True) 