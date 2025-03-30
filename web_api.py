"""
FastAPI backend for the Anthropic-powered Agent
Provides a REST API for agent functionality
"""

import os
import sys
import json
import logging
import asyncio
import uvicorn
import base64
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException, Form, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

# Import agent components
from anthropic_agent import Agent
from github_tools import get_github_tools
from claude_tools import get_claude_tools
from system_tools import get_system_tools
from anthropic_cookbook import get_cookbook_tools
from rag import get_rag_tools, RAGSystem
from image_processing import get_image_tools, ImageProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_api.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Define API models
class Message(BaseModel):
    """A message in a conversation."""
    role: str
    content: str
    timestamp: Optional[str] = None

class Conversation(BaseModel):
    """A conversation with the agent."""
    id: str
    messages: List[Message]
    model: str
    title: Optional[str] = None
    created_at: str
    updated_at: str

class MessageRequest(BaseModel):
    """Request to send a message to the agent."""
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    use_rag: Optional[bool] = False
    stream: Optional[bool] = True

class ImageMessageRequest(BaseModel):
    """Request to send a message with an image to the agent."""
    message: str
    image_path: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    use_rag: Optional[bool] = False

class ToolExecutionRequest(BaseModel):
    """Request to execute a tool."""
    tool_name: str
    parameters: Dict[str, Any]
    conversation_id: Optional[str] = None

class RAGAddDocumentRequest(BaseModel):
    """Request to add a document to the RAG system."""
    content: str
    metadata: Optional[Dict[str, Any]] = None
    chunk_strategy: Optional[str] = "tokens"

class RAGQueryRequest(BaseModel):
    """Request to query the RAG system."""
    query: str
    top_k: Optional[int] = 5
    filters: Optional[Dict[str, Any]] = None

# API security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def get_api_key() -> str:
    """Get the API key from environment variable."""
    return os.environ.get("WEB_API_KEY", "development-key")

async def validate_api_key(api_key: str = Depends(api_key_header)):
    """Validate the API key."""
    if api_key != get_api_key():
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return True

# Initialize FastAPI app
app = FastAPI(
    title="Anthropic-Powered Agent API",
    description="REST API for the Anthropic-powered Agent",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instances cache
agent_instances = {}

# In-memory conversation storage (in a real app, use a database)
conversations = {}

# File upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Image upload directory
IMAGE_DIR = UPLOAD_DIR / "images"
IMAGE_DIR.mkdir(exist_ok=True)

# Document upload directory
DOCUMENT_DIR = UPLOAD_DIR / "documents"
DOCUMENT_DIR.mkdir(exist_ok=True)

# Initialize RAG system
rag_system = RAGSystem()

def get_agent(model: str = "claude-3-opus-20240229", use_rag: bool = False) -> Agent:
    """Get or create an agent instance."""
    cache_key = f"{model}_{use_rag}"
    
    if cache_key not in agent_instances:
        logger.info(f"Creating new agent instance with model={model}, use_rag={use_rag}")
        
        # Create agent
        agent = Agent(model=model, use_rag=use_rag)
        
        # Register tools
        github_tools = get_github_tools()
        agent.register_tools(github_tools)
        
        claude_tools = get_claude_tools()
        agent.register_tools(claude_tools)
        
        system_tools = get_system_tools()
        agent.register_tools(system_tools)
        
        cookbook_tools = get_cookbook_tools()
        agent.register_tools(cookbook_tools)
        
        # Register RAG tools if enabled
        if use_rag:
            rag_tools = get_rag_tools()
            agent.register_tools(rag_tools)
        
        # Register image tools
        image_tools = get_image_tools()
        agent.register_tools(image_tools)
        
        # Store in cache
        agent_instances[cache_key] = agent
    
    return agent_instances[cache_key]

def create_conversation(model: str = "claude-3-opus-20240229") -> str:
    """Create a new conversation."""
    conversation_id = f"conv_{len(conversations) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conversations[conversation_id] = Conversation(
        id=conversation_id,
        messages=[],
        model=model,
        title=None,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    return conversation_id

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Anthropic-Powered Agent API",
        "version": "1.0.0",
        "status": "running"
    }

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

# Models endpoint
@app.get("/models")
async def get_models(api_key: bool = Depends(validate_api_key)):
    """Get available models."""
    from model_config import list_available_models
    
    return {"models": list_available_models()}

# Message endpoint
@app.post("/message")
async def send_message(request: MessageRequest, api_key: bool = Depends(validate_api_key)):
    """Send a message to the agent."""
    # Get or create conversation
    conversation_id = request.conversation_id
    if not conversation_id or conversation_id not in conversations:
        conversation_id = create_conversation(request.model or "claude-3-opus-20240229")
    
    conversation = conversations[conversation_id]
    
    # Get agent
    agent = get_agent(conversation.model, request.use_rag)
    
    # Update agent's memory with conversation history
    agent.memory.messages = []
    for msg in conversation.messages:
        agent.memory.add(msg.role, msg.content)
    
    # Process message
    if request.stream:
        return {"conversation_id": conversation_id, "streaming": True}
    else:
        response = await agent.process_message(request.message)
        
        # Update conversation
        conversation.messages.append(Message(
            role="user",
            content=request.message,
            timestamp=datetime.now().isoformat()
        ))
        
        conversation.messages.append(Message(
            role="assistant",
            content=response,
            timestamp=datetime.now().isoformat()
        ))
        
        conversation.updated_at = datetime.now().isoformat()
        
        # If no title yet, generate one
        if not conversation.title and len(conversation.messages) >= 2:
            # Use the first user message as the title
            first_message = conversation.messages[0].content
            conversation.title = (first_message[:30] + "...") if len(first_message) > 30 else first_message
        
        return {
            "conversation_id": conversation_id,
            "response": response
        }

# Message streaming endpoint
@app.websocket("/message/stream/{conversation_id}")
async def stream_message(websocket: WebSocket):
    """Stream a message response from the agent."""
    await websocket.accept()
    
    try:
        # Get WebSocket message
        data = await websocket.receive_json()
        message = data.get("message")
        model = data.get("model")
        use_rag = data.get("use_rag", False)
        conversation_id = websocket.path_params["conversation_id"]
        
        # Get or create conversation
        if not conversation_id or conversation_id not in conversations:
            conversation_id = create_conversation(model or "claude-3-opus-20240229")
        
        conversation = conversations[conversation_id]
        
        # Get agent
        agent = get_agent(conversation.model, use_rag)
        
        # Update agent's memory with conversation history
        agent.memory.messages = []
        for msg in conversation.messages:
            agent.memory.add(msg.role, msg.content)
        
        # Add user message to conversation
        conversation.messages.append(Message(
            role="user",
            content=message,
            timestamp=datetime.now().isoformat()
        ))
        
        # Send initial response
        await websocket.send_json({
            "type": "start",
            "conversation_id": conversation_id
        })
        
        # Stream response
        full_response = ""
        async for chunk in agent.stream_response(message):
            await websocket.send_json({
                "type": "chunk",
                "content": chunk
            })
            full_response += chunk
        
        # Add response to conversation
        conversation.messages.append(Message(
            role="assistant",
            content=full_response,
            timestamp=datetime.now().isoformat()
        ))
        
        conversation.updated_at = datetime.now().isoformat()
        
        # If no title yet, generate one
        if not conversation.title and len(conversation.messages) >= 2:
            # Use the first user message as the title
            first_message = conversation.messages[0].content
            conversation.title = (first_message[:30] + "...") if len(first_message) > 30 else first_message
        
        # Send completion message
        await websocket.send_json({
            "type": "end",
            "conversation_id": conversation_id
        })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
    
    finally:
        await websocket.close()

# Image message endpoint
@app.post("/message/image")
async def send_image_message(request: ImageMessageRequest, api_key: bool = Depends(validate_api_key)):
    """Send a message with an image to the agent."""
    # Verify image exists
    image_path = request.image_path
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    # Get or create conversation
    conversation_id = request.conversation_id
    if not conversation_id or conversation_id not in conversations:
        conversation_id = create_conversation(request.model or "claude-3-opus-20240229")
    
    conversation = conversations[conversation_id]
    
    # Get agent
    agent = get_agent(conversation.model, request.use_rag)
    
    # Update agent's memory with conversation history
    agent.memory.messages = []
    for msg in conversation.messages:
        agent.memory.add(msg.role, msg.content)
    
    # Process message with image
    response = await agent.process_message_with_image(request.message, image_path)
    
    # Update conversation
    conversation.messages.append(Message(
        role="user",
        content=f"[Message with image: {os.path.basename(image_path)}] {request.message}",
        timestamp=datetime.now().isoformat()
    ))
    
    conversation.messages.append(Message(
        role="assistant",
        content=response,
        timestamp=datetime.now().isoformat()
    ))
    
    conversation.updated_at = datetime.now().isoformat()
    
    # If no title yet, generate one
    if not conversation.title and len(conversation.messages) >= 2:
        # Use the first user message as the title
        conversation.title = f"Image: {os.path.basename(image_path)}"
    
    return {
        "conversation_id": conversation_id,
        "response": response
    }

# Upload image endpoint
@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...), api_key: bool = Depends(validate_api_key)):
    """Upload an image file."""
    try:
        # Create a unique filename
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        file_path = IMAGE_DIR / filename
        
        # Save the file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "filename": filename,
            "path": str(file_path),
            "size": len(content)
        }
    
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

# List conversations endpoint
@app.get("/conversations")
async def list_conversations(api_key: bool = Depends(validate_api_key)):
    """List all conversations."""
    return {
        "conversations": [
            {
                "id": conv.id,
                "title": conv.title or f"Conversation {conv.id}",
                "model": conv.model,
                "message_count": len(conv.messages),
                "created_at": conv.created_at,
                "updated_at": conv.updated_at
            }
            for conv in conversations.values()
        ]
    }

# Get conversation endpoint
@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, api_key: bool = Depends(validate_api_key)):
    """Get a specific conversation."""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    return conversations[conversation_id]

# Delete conversation endpoint
@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, api_key: bool = Depends(validate_api_key)):
    """Delete a specific conversation."""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    del conversations[conversation_id]
    
    return {"status": "success", "message": f"Conversation {conversation_id} deleted"}

# Tool execution endpoint
@app.post("/tools/execute")
async def execute_tool(request: ToolExecutionRequest, api_key: bool = Depends(validate_api_key)):
    """Execute a tool directly."""
    # Get agent (use default model and RAG settings)
    agent = get_agent()
    
    # Check if tool exists
    if request.tool_name not in agent.tools:
        raise HTTPException(status_code=404, detail=f"Tool {request.tool_name} not found")
    
    tool = agent.tools[request.tool_name]
    
    # Check required parameters
    missing_params = []
    for param in tool.parameters:
        if param.required and param.name not in request.parameters:
            missing_params.append(param.name)
    
    if missing_params:
        raise HTTPException(
            status_code=400, 
            detail=f"Missing required parameters: {', '.join(missing_params)}"
        )
    
    # Execute tool
    try:
        if asyncio.iscoroutinefunction(tool.function):
            result = await tool.function(**request.parameters)
        else:
            result = tool.function(**request.parameters)
        
        # If conversation_id provided, add to conversation
        if request.conversation_id and request.conversation_id in conversations:
            conversation = conversations[request.conversation_id]
            
            # Add tool execution to conversation
            conversation.messages.append(Message(
                role="user",
                content=f"[Tool execution: {request.tool_name}]",
                timestamp=datetime.now().isoformat()
            ))
            
            # Add result to conversation
            result_str = json.dumps(result, indent=2)
            conversation.messages.append(Message(
                role="assistant",
                content=f"[Tool result]\n```json\n{result_str}\n```",
                timestamp=datetime.now().isoformat()
            ))
            
            conversation.updated_at = datetime.now().isoformat()
        
        return {
            "tool": request.tool_name,
            "parameters": request.parameters,
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Error executing tool {request.tool_name}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error executing tool {request.tool_name}: {str(e)}"
        )

# List tools endpoint
@app.get("/tools")
async def list_tools(category: Optional[str] = None, api_key: bool = Depends(validate_api_key)):
    """List available tools."""
    # Get agent
    agent = get_agent()
    
    if category:
        if category not in agent.tool_categories:
            raise HTTPException(status_code=404, detail=f"Category {category} not found")
        
        tools = {name: agent.tools[name] for name in agent.tool_categories[category]}
    else:
        tools = agent.tools
    
    # Format tools
    formatted_tools = []
    for name, tool in tools.items():
        formatted_tools.append({
            "name": name,
            "description": tool.description,
            "category": tool.category,
            "parameters": [
                {
                    "name": param.name,
                    "type": param.type,
                    "description": param.description,
                    "required": param.required,
                    "default": param.default
                }
                for param in tool.parameters
            ]
        })
    
    return {"tools": formatted_tools}

# RAG endpoints
@app.post("/rag/documents")
async def add_rag_document(request: RAGAddDocumentRequest, api_key: bool = Depends(validate_api_key)):
    """Add a document to the RAG system."""
    try:
        document = await rag_system.add_document(
            content=request.content,
            metadata=request.metadata,
            chunk_strategy=request.chunk_strategy
        )
        
        return {
            "document_id": document.id,
            "chunk_count": len(document.chunks),
            "metadata": document.metadata
        }
    
    except Exception as e:
        logger.error(f"Error adding document to RAG: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error adding document to RAG: {str(e)}"
        )

@app.post("/rag/documents/file")
async def add_rag_document_file(
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
    chunk_strategy: str = Form("tokens"),
    api_key: bool = Depends(validate_api_key)
):
    """Add a document file to the RAG system."""
    try:
        # Parse metadata
        metadata_dict = json.loads(metadata)
        
        # Create a unique filename
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        file_path = DOCUMENT_DIR / filename
        
        # Save the file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Add file metadata
        metadata_dict["source"] = str(file_path)
        metadata_dict["filename"] = file.filename
        metadata_dict["upload_time"] = datetime.now().isoformat()
        
        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            document_content = f.read()
        
        # Add to RAG system
        document = await rag_system.add_document(
            content=document_content,
            metadata=metadata_dict,
            chunk_strategy=chunk_strategy
        )
        
        return {
            "document_id": document.id,
            "filename": file.filename,
            "chunk_count": len(document.chunks),
            "metadata": document.metadata
        }
    
    except Exception as e:
        logger.error(f"Error adding document file to RAG: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error adding document file to RAG: {str(e)}"
        )

@app.get("/rag/documents")
async def list_rag_documents(api_key: bool = Depends(validate_api_key)):
    """List all documents in the RAG system."""
    try:
        documents = rag_system.get_all_documents()
        
        return {
            "document_count": len(documents),
            "documents": [
                {
                    "id": doc.id,
                    "content_preview": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content,
                    "metadata": doc.metadata,
                    "chunk_count": len(doc.chunks)
                }
                for doc in documents
            ]
        }
    
    except Exception as e:
        logger.error(f"Error listing RAG documents: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error listing RAG documents: {str(e)}"
        )

@app.get("/rag/documents/{document_id}")
async def get_rag_document(document_id: str, api_key: bool = Depends(validate_api_key)):
    """Get a document from the RAG system."""
    try:
        document = rag_system.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        
        return {
            "id": document.id,
            "content": document.content,
            "metadata": document.metadata,
            "chunk_count": len(document.chunks),
            "chunks": [
                {
                    "id": chunk["id"],
                    "index": chunk["index"]
                }
                for chunk in document.chunks
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RAG document: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error getting RAG document: {str(e)}"
        )

@app.delete("/rag/documents/{document_id}")
async def delete_rag_document(document_id: str, api_key: bool = Depends(validate_api_key)):
    """Delete a document from the RAG system."""
    try:
        success = rag_system.delete_document(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        
        return {"success": True, "document_id": document_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting RAG document: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error deleting RAG document: {str(e)}"
        )

@app.post("/rag/query")
async def query_rag(request: RAGQueryRequest, api_key: bool = Depends(validate_api_key)):
    """Query the RAG system."""
    try:
        results = await rag_system.query(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters
        )
        
        return results
    
    except Exception as e:
        logger.error(f"Error querying RAG: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error querying RAG: {str(e)}"
        )

@app.get("/rag/stats")
async def get_rag_stats(api_key: bool = Depends(validate_api_key)):
    """Get statistics about the RAG system."""
    try:
        stats = rag_system.get_stats()
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting RAG stats: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error getting RAG stats: {str(e)}"
        )

# Serve static files for the React frontend
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

# Serve the main React app
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve the React frontend."""
    # If requesting an API endpoint, return 404 to let the API handler handle it
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Otherwise, serve the React app
    return FileResponse("frontend/build/index.html")

# Start the server
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start the web API server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to listen on")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print(f"Starting web API server on {args.host}:{args.port}")
    uvicorn.run("web_api:app", host=args.host, port=args.port, reload=args.reload)