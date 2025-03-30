"""
Unit tests for Claude tools
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from claude_tools import get_claude_tools

class TestClaudeTools(unittest.TestCase):
    """Test cases for Claude tools."""
    
    @patch('claude_tools.client')
    def test_get_claude_tools(self, mock_client):
        """Test getting Claude tools."""
        # Mock client response
        mock_content = MagicMock()
        mock_content.text = "Mocked Claude response"
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        
        # Get Claude tools
        tools = get_claude_tools()
        
        # Check if tools are correct
        self.assertIsInstance(tools, list)
        self.assertTrue(len(tools) > 0)
        
        # Check tool structure
        for tool in tools:
            self.assertTrue(hasattr(tool, 'name'))
            self.assertTrue(hasattr(tool, 'description'))
            self.assertTrue(hasattr(tool, 'parameters'))
            self.assertTrue(hasattr(tool, 'function'))
            self.assertTrue(hasattr(tool, 'category'))
            self.assertEqual(tool.category, 'claude')
    
    @patch('claude_tools.client')
    async def test_summarize_text_tool(self, mock_client):
        """Test summarize_text tool."""
        # Mock client response
        mock_content = MagicMock()
        mock_content.text = "This is a summary."
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        
        # Get Claude tools
        tools = get_claude_tools()
        
        # Find the summarize_text tool
        summarize_tool = next(tool for tool in tools if tool.name == "summarize_text")
        
        # Execute the tool
        result = await summarize_tool.function(text="Test text to summarize")
        
        # Check if result is correct
        self.assertEqual(result["summary"], "This is a summary.")
        
        # Check if client was called correctly
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args[1]
        self.assertEqual(call_args["model"], "claude-3-opus-20240229")
        self.assertIn("Summarize the following text", call_args["messages"][0]["content"])