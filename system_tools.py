import os
import json
import shlex
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from typing import List, Dict, Any, Optional
from anthropic_agent.tools import Tool, ToolParameter

def get_system_tools() -> List[Tool]:
    """Get tools for system operations."""
    
    async def read_file(path: str) -> Dict[str, Any]:
        """Read the contents of a file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"content": content}
        except Exception as e:
            return {"error": str(e)}
    
    async def write_file(path: str, content: str) -> Dict[str, Any]:
        """Write content to a file."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success"}
        except Exception as e:
            return {"error": str(e)}
    
    async def execute_command(command: str) -> Dict[str, Any]:
        """Execute a system command."""
        try:
            result = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return {
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
                "returncode": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def analyze_csv(file_path: str) -> Dict[str, Any]:
        """Analyze a CSV file and return summary statistics."""
        try:
            data = pd.read_csv(file_path)
            summary = data.describe().to_dict()
            return {"summary": summary}
        except Exception as e:
            return {"error": str(e)}
    
    async def plot_data(data: str, x: str, y: str, output_path: str) -> Dict[str, Any]:
        """Plot data from a JSON string and save the plot to a file."""
        try:
            df = pd.read_json(data)
            plt.figure(figsize=(10, 6))
            plt.plot(df[x], df[y])
            plt.xlabel(x)
            plt.ylabel(y)
            plt.title(f"{y} vs {x}")
            plt.savefig(output_path)
            return {"status": "success", "output_path": output_path}
        except Exception as e:
            return {"error": str(e)}
    
    # Define tools
    return [
        Tool(
            name="read_file",
            description="Read the contents of a file",
            parameters=[
                ToolParameter(name="path", type="string", description="Path to the file")
            ],
            function=read_file,
            category="system"
        ),
        
        Tool(
            name="write_file",
            description="Write content to a file",
            parameters=[
                ToolParameter(name="path", type="string", description="Path to the file"),
                ToolParameter(name="content", type="string", description="Content to write")
            ],
            function=write_file,
            category="system"
        ),
        
        Tool(
            name="execute_command",
            description="Execute a system command",
            parameters=[
                ToolParameter(name="command", type="string", description="Command to execute")
            ],
            function=execute_command,
            category="system"
        ),
        
        Tool(
            name="analyze_csv",
            description="Analyze a CSV file and return summary statistics",
            parameters=[
                ToolParameter(name="file_path", type="string", description="Path to the CSV file")
            ],
            function=analyze_csv,
            category="system"
        ),
        
        Tool(
            name="plot_data",
            description="Plot data from a JSON string and save the plot to a file",
            parameters=[
                ToolParameter(name="data", type="string", description="JSON string of the data"),
                ToolParameter(name="x", type="string", description="Column name for x-axis"),
                ToolParameter(name="y", type="string", description="Column name for y-axis"),
                ToolParameter(name="output_path", type="string", description="Path to