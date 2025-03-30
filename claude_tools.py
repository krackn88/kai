from anthropic import Anthropic, Client
from typing import List, Dict, Any
from anthropic_agent.tools import Tool, ToolParameter

# Initialize Anthropic client
client = Client(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def get_claude_tools() -> List[Tool]:
    """Get tools for Claude language capabilities."""
    
    async def summarize_text(text: str) -> Dict[str, Any]:
        """Summarize a given text using Claude."""
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize the following text:\n\n{text}"
                }
            ]
        )
        return {"summary": response.content[0].text}
    
    async def translate_text(text: str, target_language: str) -> Dict[str, Any]:
        """Translate a given text to the target language using Claude."""
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"Translate the following text to {target_language}:\n\n{text}"
                }
            ]
        )
        return {"translation": response.content[0].text}
    
    async def complete_code(prompt: str) -> Dict[str, Any]:
        """Generate code completion for a given prompt using Claude."""
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"Complete the following code:\n\n{prompt}"
                }
            ]
        )
        return {"completion": response.content[0].text}
    
    async def explain_code(code: str) -> Dict[str, Any]:
        """Explain a given piece of code using Claude."""
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"Explain the following code:\n\n{code}"
                }
            ]
        )
        return {"explanation": response.content[0].text}
    
    # Define tools
    return [
        Tool(
            name="summarize_text",
            description="Summarize a given text using Claude",
            parameters=[
                ToolParameter(name="text", type="string", description="Text to summarize")
            ],
            function=summarize_text,
            category="claude"
        ),
        
        Tool(
            name="translate_text",
            description="Translate a given text to the target language using Claude",
            parameters=[
                ToolParameter(name="text", type="string", description="Text to translate"),
                ToolParameter(name="target_language", type="string", description="Target language")
            ],
            function=translate_text,
            category="claude"
        ),
        
        Tool(
            name="complete_code",
            description="Generate code completion for a given prompt using Claude",
            parameters=[
                ToolParameter(name="prompt", type="string", description="Code prompt")
            ],
            function=complete_code,
            category="claude"
        ),
        
        Tool(
            name="explain_code",
            description="Explain a given piece of code using Claude",
            parameters=[
                ToolParameter(name="code", type="string", description="Code to explain")
            ],
            function=explain_code,
            category="claude"
        )
    ]