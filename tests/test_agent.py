"""
Unit tests for the Anthropic-powered Agent
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, patch
import json

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from anthropic_agent import Agent
from anthropic_agent.memory import Memory
from anthropic_agent.tools import Tool, ToolParameter

class TestAgent(unittest.TestCase):
    """Test cases for the Agent class."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'ANTHROPIC_API_KEY': 'mock-api-key',
        })
        self.env_patcher.start()
        
        # Create agent with mocked client
        self.agent = Agent(model="claude-3-haiku-20240307")
        self.agent.client = MagicMock()
        
        # Set up mock response
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "This is a test response."
        mock_content.type = "text"
        mock_response.content = [mock_content]
        self.agent.client.messages.create.return_value = mock_response
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
    
    def test_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.model, "claude-3-haiku-20240307")
        self.assertIsInstance(self.agent.memory, Memory)
        self.assertEqual(len(self.agent.tools), 0)
        self.assertEqual(len(self.agent.tool_categories), 0)
        self.assertFalse(self.agent.use_rag)
    
    def test_register_tools(self):
        """Test tool registration."""
        # Create mock tools
        mock_tool1 = Tool(
            name="test_tool1",
            description="Test tool 1",
            parameters=[
                ToolParameter(name="param1", type="string", description="Test parameter")
            ],
            function=lambda param1: {"result": param1},
            category="test"
        )
        
        mock_tool2 = Tool(
            name="test_tool2",
            description="Test tool 2",
            parameters=[],
            function=lambda: {"result": "success"},
            category="test"
        )
        
        # Register tools
        self.agent.register_tools([mock_tool1, mock_tool2])
        
        # Check if tools are registered correctly
        self.assertEqual(len(self.agent.tools), 2)
        self.assertIn("test_tool1", self.agent.tools)
        self.assertIn("test_tool2", self.agent.tools)
        
        # Check if tool categories are updated
        self.assertIn("test", self.agent.tool_categories)
        self.assertEqual(len(self.agent.tool_categories["test"]), 2)
        self.assertIn("test_tool1", self.agent.tool_categories["test"])
        self.assertIn("test_tool2", self.agent.tool_categories["test"])
    
    def test_system_prompt_enrichment(self):
        """Test system prompt enrichment."""
        # Test basic enrichment
        enriched_prompt = self.agent._enrich_system_prompt()
        self.assertIn("powered by Anthropic's Claude model", enriched_prompt)
        
        # Test with RAG enabled
        self.agent.use_rag = True
        enriched_prompt = self.agent._enrich_system_prompt()
        self.assertIn("access to a knowledge base", enriched_prompt)
    
    @patch('anthropic_agent.Agent._update_usage_stats')
    async def test_process_message(self, mock_update_stats):
        """Test message processing."""
        # Process a message
        response = await self.agent.process_message("Hello, Claude!")
        
        # Check if response is correct
        self.assertEqual(response, "This is a test response.")
        
        # Check if memory is updated
        self.assertEqual(len(self.agent.memory.messages), 2)
        self.assertEqual(self.agent.memory.messages[0]["role"], "user")
        self.assertEqual(self.agent.memory.messages[0]["content"], "Hello, Claude!")
        self.assertEqual(self.agent.memory.messages[1]["role"], "assistant")
        self.assertEqual(self.agent.memory.messages[1]["content"], "This is a test response.")
        
        # Check if client was called correctly
        self.agent.client.messages.create.assert_called_once()
        call_args = self.agent.client.messages.create.call_args[1]
        self.assertEqual(call_args["model"], "claude-3-haiku-20240307")
        self.assertIsInstance(call_args["messages"], list)
        
        # Check if usage stats were updated
        mock_update_stats.assert_called_once()

class TestMemory(unittest.TestCase):
    """Test cases for the Memory class."""
    
    def setUp(self):
        """Set up test environment."""
        self.memory = Memory(max_messages=5)
    
    def test_initialization(self):
        """Test memory initialization."""
        self.assertEqual(len(self.memory.messages), 0)
        self.assertEqual(self.memory.max_messages, 5)
    
    def test_add_message(self):
        """Test adding messages."""
        # Add user message
        self.memory.add("user", "Hello")
        self.assertEqual(len(self.memory.messages), 1)
        self.assertEqual(self.memory.messages[0]["role"], "user")
        self.assertEqual(self.memory.messages[0]["content"], "Hello")
        
        # Add assistant message
        self.memory.add("assistant", "Hi there!")
        self.assertEqual(len(self.memory.messages), 2)
        self.assertEqual(self.memory.messages[1]["role"], "assistant")
        self.assertEqual(self.memory.messages[1]["content"], "Hi there!")
    
    def test_memory_limit(self):
        """Test memory limit enforcement."""
        # Add more messages than the limit
        for i in range(10):
            self.memory.add("user" if i % 2 == 0 else "assistant", f"Message {i}")
        
        # Check if memory limit is enforced
        self.assertEqual(len(self.memory.messages), 5)
        
        # Check if oldest messages are removed
        self.assertEqual(self.memory.messages[0]["content"], "Message 5")
        self.assertEqual(self.memory.messages[4]["content"], "Message 9")
    
    def test_get_history(self):
        """Test getting conversation history."""
        # Add messages
        self.memory.add("user", "Hello")
        self.memory.add("assistant", "Hi there!")
        self.memory.add("user", "How are you?")
        
        # Get history
        history = self.memory.get_history()
        
        # Check if history is correct
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "Hello")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "Hi there!")
        self.assertEqual(history[2]["role"], "user")
        self.assertEqual(history[2]["content"], "How are you?")
    
    def test_clear(self):
        """Test clearing memory."""
        # Add messages
        self.memory.add("user", "Hello")
        self.memory.add("assistant", "Hi there!")
        
        # Clear memory
        self.memory.clear()
        
        # Check if memory is cleared
        self.assertEqual(len(self.memory.messages), 0)