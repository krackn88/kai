from typing import List, Dict, Any
from anthropic_agent.tools import Tool, ToolParameter
from anthropic import Anthropic, Client

# Initialize Anthropic client
client = Client(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def get_cookbook_tools() -> List[Tool]:
    """Get tools for advanced techniques from Anthropic's cookbook."""
    
    async def few_shot_prompting(prompt: str, examples: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate a response using few-shot prompting."""
        messages = [{"role": "user", "content": prompt}]
        
        for example in examples:
            messages.append({"role": "system", "content": example["system"]})
            messages.append({"role": "user", "content": example["user"]})
        
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=messages
        )
        return {"response": response.content[0].text}
    
    async def chain_of_thought(prompt: str) -> Dict[str, Any]:
        """Generate a response using chain-of-thought reasoning."""
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"Think step by step and provide a detailed response to the following prompt:\n\n{prompt}"
                }
            ]
        )
        return {"response": response.content[0].text}
    
    # Define tools
    return [
        Tool(
            name="few_shot_prompting",
            description="Generate a response using few-shot prompting",
            parameters=[
                ToolParameter(name="prompt", type="string", description="Prompt for Claude"),
                ToolParameter(name="examples", type="array", description="Examples for few-shot prompting")
            ],
            function=few_shot_prompting,
            category="cookbook"
        ),
        
        Tool(
            name="chain_of_thought",
            description="Generate a response using chain-of-thought reasoning",
            parameters=[
                ToolParameter(name="prompt", type="string", description="Prompt for Claude")
            ],
            function=chain_of_thought,
            category="cookbook"
        )
    ]