"""
Unit tests for web API
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import json
from fastapi.testclient import TestClient

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the web API app
from web_api import app, get_agent, create_conversation, get_api_key

# Create test client
client = TestClient(app)

class TestWebAPI(unittest.TestCase):
    """Test cases for the web API."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'ANTHROPIC_API_KEY': 'mock-api-key',
            'WEB_API_KEY': 'test-api-key',
        })
        self.env_patcher.start()
        
        # Mock agent
        self.agent_patcher = patch('web_api.Agent')
        self.mock_agent_class = self.agent_patcher.start()
        self.mock_agent = MagicMock()
        self.mock_agent.process_message = AsyncMock(return_value="Test response")
        self.mock_agent.process_message_with_image = AsyncMock(return_value="Test image response")
        self.mock_agent.memory = MagicMock()
        self.mock_agent.memory.add = MagicMock()
        self.mock_agent_class.return_value = self.mock_agent
        
        # Override get_agent function
        self.get_agent_patcher = patch('web_api.get_agent', return_value=self.mock_agent)
        self.get_agent_patcher.start()
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
        self.agent_patcher.stop()
        self.get_agent_patcher.stop()
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        # Make request
        response = client.get("/")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Anthropic-Powered Agent API")
        self.assertEqual(data["status"], "running")
    
    def test_health_endpoint(self):
        """Test the health endpoint."""
        # Make request
        response = client.get("/health")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
    
    def test_message_endpoint(self):
        """Test the message endpoint."""
        # Make request
        response = client.post(
            "/message",
            json={"message": "Hello", "stream": False},
            headers={"X-API-Key": "test-api-key"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("conversation_id", data)
        self.assertEqual(data["response"], "Test response")
        
        # Check if agent was called correctly
        self.mock_agent.process_message.assert_called_once_with("Hello")
    
    def test_tools_endpoint(self):
        """Test the tools endpoint."""
        # Mock agent tools
        self.mock_agent.tools = {
            "test_tool": MagicMock(
                name="test_tool",
                description="Test tool",
                category="test",
                parameters=[MagicMock(
                    name="param1",
                    type="string",
                    description="Test parameter",
                    required=True,
                    default=None
                )]
            )
        }
        self.mock_agent.tool_categories = {"test": ["test_tool"]}
        
        # Make request
        response = client.get(
            "/tools",
            headers={"X-API-Key": "test-api-key"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("tools", data)
        self.assertEqual(len(data["tools"]), 1)
        self.assertEqual(data["tools"][0]["name"], "test_tool")
        self.assertEqual(data["tools"][0]["category"], "test")
    
    def test_invalid_api_key(self):
        """Test invalid API key."""
        # Make request with invalid API key
        response = client.get(
            "/tools",
            headers={"X-API-Key": "invalid-key"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data["detail"], "Invalid API key")