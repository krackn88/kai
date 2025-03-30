import os
import json
import shlex
import asyncio
import signal
import readline
from datetime import datetime
from typing import List, Optional
from anthropic_agent import Agent
from structured_schemas import (
    TextAnalysisResponse, 
    SearchResultsResponse, 
    GitHubRepositoryAnalysis,
    CodeAnalysisResponse,
    PlanResponse
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentCLI:
    """Command Line Interface for the Anthropic Agent."""
    
    def __init__(self, agent: Agent, use_streaming: bool = True):
        """Initialize with an agent."""
        self.agent = agent
        self.running = True
        self.history = []
        self.use_streaming = use_streaming
        self.commands = {
            "help": self.show_help,
            "exit": self.exit,
            "quit": self.exit,
            "tools": self.list_tools,
            "clear": self.clear_screen,
            "history": self.show_history,
            "save": self.save_conversation,
            "load": self.load_conversation,
            "github": self.github_commands,
            "execute": self.execute_tool,
            "streaming": self.toggle_streaming,
            "models": self.model_commands,
            "usage": self.show_usage_stats,
            "structured": self.structured_commands,
            "rag": self.rag_commands,
            "image": self.image_commands  # Add image commands
        }
        
        # Available structured output schemas
        self.structured_schemas = {
            "text_analysis": TextAnalysisResponse,
            "search_results": SearchResultsResponse,
            "github_repo": GitHubRepositoryAnalysis,
            "code_analysis": CodeAnalysisResponse,
            "plan": PlanResponse
        }
    
    # ... existing methods ...
    
    def image_commands(self, args: Optional[List[str]] = None) -> None:
        """Handle image-related commands."""
        if not args or args[0] == "help":
            print("\nImage Commands:")
            print("  image analyze <image_path> - Analyze an image with a prompt")
            print("  image ocr <image_path>     - Extract text from an image")
            print("  image describe <image_path> - Generate a description of an image")
            print("  image optimize <image_path> - Optimize an image for Claude")
            print("  image download <image_url>  - Download an image from a URL")
            print("  image send <image_path>     - Send a message with an image")
            return
        
        command = args[0]
        
        if command == "analyze" and len(args) >= 2:
            image_path = args[1]
            if not os.path.exists(image_path):
                print(f"Error: Image file not found: {image_path}")
                return
            
            # Get prompt from user
            prompt = input("Enter analysis prompt: ")
            
            self.execute_tool(["analyze_image", f"image_path={image_path}", f"prompt={prompt}"])
        
        elif command == "ocr" and len(args) >= 2:
            image_path = args[1]
            if not os.path.exists(image_path):
                print(f"Error: Image file not found: {image_path}")
                return
            
            self.execute_tool(["extract_text_from_image", f"image_path={image_path}"])
        
        elif command == "describe" and len(args) >= 2:
            image_path = args[1]
            if not os.path.exists(image_path):
                print(f"Error: Image file not found: {image_path}")
                return
            
            detail_level = "detailed"
            if len(args) >= 3 and args[2] in ["brief", "detailed", "comprehensive"]:
                detail_level = args[2]
            
            self.execute_tool(["describe_image", f"image_path={image_path}", f"detail_level={detail_level}"])
        
        elif command == "optimize" and len(args) >= 2:
            image_path = args[1]
            if not os.path.exists(image_path):
                print(f"Error: Image file not found: {image_path}")
                return
            
            max_size = 5.0
            if len(args) >= 3 and args[2].replace(".", "").isdigit():
                max_size = float(args[2])
            
            self.execute_tool(["optimize_image", f"image_path={image_path}", f"max_size_mb={max_size}"])
        
        elif command == "download" and len(args) >= 2:
            image_url = args[1]
            
            self.execute_tool(["download_image", f"image_url={image_url}"])
        
        elif command == "send" and len(args) >= 2:
            image_path = args[1]
            if not os.path.exists(image_path):
                print(f"Error: Image file not found: {image_path}")
                return
            
            # Get message from user
            message = input("Enter your message to send with the image: ")
            
            # Process message with image
            print("Agent is thinking...")
            response = asyncio.run(self.agent.process_message_with_image(message, image_path))
            
            print("\nAgent:")
            print(response)
            print()
            
            # Add to history
            self.history.append(("user", f"[Message with image: {os.path.basename(image_path)}] {message}"))
            self.history.append(("assistant", response))
        
        else:
            print(f"Unknown image command: {command}")
            print("Use 'image help' to see available commands.")

    def show_help(self, args: Optional[List[str]] = None) -> None:
        """Show help information."""
        print("\n===== Anthropic Agent CLI Help =====")
        print("\nAvailable Commands:")
        print("  help              - Show this help message")
        print("  exit, quit        - Exit the program")
        print("  tools [category]  - List available tools, optionally filtered by category")
        print("  clear             - Clear the screen")
        print("  history [n]       - Show conversation history (last n messages)")
        print("  save <filename>   - Save conversation to a file")
        print("  load <filename>   - Load conversation from a file")
        print("  github help       - Show GitHub commands")
        print("  execute <tool>    - Execute a tool directly")
        print("  streaming on|off  - Toggle streaming mode")
        print("  models            - Show model information and commands")
        print("  usage             - Show current usage statistics")
        print("  structured        - Show structured output commands")
        print("  image             - Show image processing commands")
        
        if self.agent.use_rag:
            print("  rag               - Show RAG system commands")
        
        print("\nAny other input will be processed as a query to the agent.")
        print("\n===================================\n")