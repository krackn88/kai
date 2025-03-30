import base64
import mimetypes
from typing import Dict, List, Optional, Any, Union, BinaryIO, Type, Tuple
from anthropic import Anthropic, Client, Model
from anthropic_agent.memory import Memory
from anthropic_agent.tools import Tool, ToolParameter

class Agent:
    """Anthropic-powered agent with tool execution capabilities."""
    
    def __init__(self, model: str = "claude-3-opus-20240229", use_rag: bool = False):
        self.model = model
        self.memory = Memory()
        self.tools = {}
        self.tool_categories = {}
        self.client = Client(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.use_rag = use_rag
        self.rag_system = RAGSystem() if use_rag else None
    
    def register_tools(self, tools: List[Tool]):
        """Register tools with the agent."""
        for tool in tools:
            self.tools[tool.name] = tool
            if tool.category not in self.tool_categories:
                self.tool_categories[tool.category] = []
            self.tool_categories[tool.category].append(tool.name)
    
    def _enrich_system_prompt(self) -> str:
        """Enrich the system prompt with context."""
        enriched = "You are an assistant powered by Anthropic's Claude model. You have access to various tools and a knowledge base."
        
        # If using RAG, mention it
        if self.use_rag:
            enriched += "\n\nYou have access to a knowledge base of documents. When appropriate, reference information from this knowledge base in your responses."
        
        return enriched
    
    async def process_message(self, user_message: str) -> str:
        """Process a user message and generate a complete response."""
        # Add user message to memory
        self.memory.add("user", user_message)
        
        # Get RAG context if enabled
        rag_context = ""
        if self.use_rag:
            rag_context = await self._enrich_with_rag(user_message)
        
        # Prepare messages
        enriched_system_prompt = self._enrich_system_prompt()
        messages = [
            {"role": "system", "content": enriched_system_prompt}
        ] + self.memory.get_history()
        
        # If RAG context is available, add it before the user's message
        if rag_context:
            # Find the last user message
            for i in range(len(messages) - 1, -1, -1):
                if messages[i]["role"] == "user":
                    # Replace with the enriched version
                    original_message = messages[i]["content"]
                    messages[i]["content"] = f"{rag_context}\n\nUser query: {original_message}\n\nPlease use the above context to help answer the query."
                    break
        
        # Prepare API call
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.7,
        }
        
        if self.tools:
            kwargs["tools"] = self._get_tool_definitions()
        
        try:
            # Call the model
            response = self.client.messages.create(**kwargs)
            
            # Update usage statistics
            self._update_usage_stats(response)
            
            # Process response
            if hasattr(response, 'content'):
                text_blocks = [block.text for block in response.content if block.type == 'text']
                assistant_response = ''.join(text_blocks)
                self.memory.add("assistant", assistant_response)
                return assistant_response
            else:
                return "I apologize, but I encountered an issue processing your request with the image."
        
        except Exception as e:
            logger.error(f"API call error: {str(e)}")
            return f"I encountered an error while processing your request with the image: {str(e)}"
    
    async def process_message_with_image(self, user_message: str, image_path: str) -> str:
        """Process a user message with an image and generate a response."""
        # Add user message to memory
        self.memory.add("user", f"[Message with image] {user_message}")
        
        # Prepare messages
        enriched_system_prompt = self._enrich_system_prompt()
        messages = [
            {"role": "system", "content": enriched_system_prompt}
        ]
        
        # Add conversation history excluding the last message (which will be replaced)
        history = self.memory.get_history()[:-1]  # Exclude the last message we just added
        messages.extend(history)
        
        # Get RAG context if enabled
        rag_context = ""
        if self.use_rag:
            rag_context = await self._enrich_with_rag(user_message)
        
        # Prepare the multimodal message
        try:
            from image_processing import ImageProcessor
            # Encode image
            image_content = ImageProcessor.encode_image_base64(image_path)
            
            # Create multimodal message content
            multimodal_content = [
                {
                    "type": "text",
                    "text": f"{rag_context}\n\n{user_message}" if rag_context else user_message
                },
                image_content
            ]
            
            # Add to messages
            messages.append({
                "role": "user",
                "content": multimodal_content
            })
            
        except Exception as e:
            # Fall back to text-only if image processing fails
            logger.error(f"Error processing image: {str(e)}")
            messages.append({
                "role": "user",
                "content": f"{rag_context}\n\n{user_message} [Note: Failed to process image: {str(e)}]" if rag_context else f"{user_message} [Note: Failed to process image: {str(e)}]"
            })
        
        # Prepare API call
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.7,
        }
        
        if self.tools:
            kwargs["tools"] = self._get_tool_definitions()
        
        try:
            # Call the model
            response = self.client.messages.create(**kwargs)
            
            # Update usage statistics
            self._update_usage_stats(response)
            
            # Process response
            if hasattr(response, 'content'):
                text_blocks = [block.text for block in response.content if block.type == 'text']
                assistant_response = ''.join(text_blocks)
                self.memory.add("assistant", assistant_response)
                return assistant_response
            else:
                return "I apologize, but I encountered an issue processing your request with the image."
        
        except Exception as e:
            logger.error(f"API call error: {str(e)}")
            return f"I encountered an error while processing your request with the image: {str(e)}"