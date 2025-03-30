"""
Unit tests for system tools
"""

import os
import sys
import unittest
import tempfile
from unittest.mock import MagicMock, patch
import json
import pandas as pd

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from system_tools import get_system_tools

class TestSystemTools(unittest.TestCase):
    """Test cases for system tools."""
    
    def test_get_system_tools(self):
        """Test getting system tools."""
        # Get system tools
        tools = get_system_tools()
        
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
            self.assertEqual(tool.category, 'system')
    
    async def test_read_file_tool(self):
        """Test read_file tool."""
        # Get system tools
        tools = get_system_tools()
        
        # Find the read_file tool
        read_file_tool = next(tool for tool in tools if tool.name == "read_file")
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("Test file content")
            tmp_path = tmp.name
        
        try:
            # Execute the tool
            result = await read_file_tool.function(path=tmp_path)
            
            # Check if result is correct
            self.assertEqual(result["content"], "Test file content")
        finally:
            # Clean up
            os.unlink(tmp_path)
    
    async def test_write_file_tool(self):
        """Test write_file tool."""
        # Get system tools
        tools = get_system_tools()
        
        # Find the write_file tool
        write_file_tool = next(tool for tool in tools if tool.name == "write_file")
        
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Execute the tool
            result = await write_file_tool.function(path=tmp_path, content="Test content to write")
            
            # Check if result is correct
            self.assertEqual(result["status"], "success")
            
            # Check if file was written correctly
            with open(tmp_path, 'r') as f:
                content = f.read()
                self.assertEqual(content, "Test content to write")
        finally:
            # Clean up
            os.unlink(tmp_path)