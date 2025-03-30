"""
Unit tests for GitHub tools
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from github_tools import GitHubAPI, get_github_tools

class TestGitHubAPI(unittest.TestCase):
    """Test cases for the GitHubAPI class."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'GITHUB_TOKEN': 'mock-github-token',
        })
        self.env_patcher.start()
        
        # Create API instance
        self.api = GitHubAPI()
        
        # Mock requests
        self.requests_patcher = patch('github_tools.requests')
        self.mock_requests = self.requests_patcher.start()
        
        # Set up mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        self.mock_requests.get.return_value = mock_response
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
        self.requests_patcher.stop()
    
    def test_initialization(self):
        """Test GitHubAPI initialization."""
        self.assertEqual(self.api.token, 'mock-github-token')
        self.assertEqual(self.api.headers["Authorization"], "token mock-github-token")
        self.assertEqual(self.api.headers["Accept"], "application/vnd.github.v3+json")
    
    def test_get_request(self):
        """Test GET request."""
        # Make a GET request
        response = self.api.get("https://api.github.com/repos/owner/repo")
        
        # Check if response is correct
        self.assertEqual(response, {"success": True})
        
        # Check if requests was called correctly
        self.mock_requests.get.assert_called_once_with(
            "https://api.github.com/repos/owner/repo",
            headers=self.api.headers,
            params=None
        )
    
    def test_get_request_with_params(self):
        """Test GET request with parameters."""
        # Make a GET request with parameters
        params = {"state": "open"}
        response = self.api.get("https://api.github.com/repos/owner/repo/issues", params=params)
        
        # Check if response is correct
        self.assertEqual(response, {"success": True})
        
        # Check if requests was called correctly
        self.mock_requests.get.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/issues",
            headers=self.api.headers,
            params=params
        )

class TestGitHubTools(unittest.TestCase):
    """Test cases for GitHub tools."""
    
    @patch('github_tools.GitHubAPI')
    def test_get_github_tools(self, mock_api_class):
        """Test getting GitHub tools."""
        # Mock GitHubAPI
        mock_api = MagicMock()
        mock_api.get.return_value = {"success": True}
        mock_api_class.return_value = mock_api
        
        # Get GitHub tools
        tools = get_github_tools()
        
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
            self.assertEqual(tool.category, 'github')