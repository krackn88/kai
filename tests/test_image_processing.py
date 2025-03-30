"""
Unit tests for image processing
"""

import os
import sys
import unittest
import tempfile
from unittest.mock import MagicMock, patch
import base64
from pathlib import Path
import shutil

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from image_processing import ImageProcessor, ImageAnalyzer, get_image_tools

class TestImageProcessor(unittest.TestCase):
    """Test cases for the ImageProcessor class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test image
        self.test_image_dir = Path(tempfile.mkdtemp())
        self.test_image_path = self.test_image_dir / "test_image.jpg"
        
        # Create a simple 1x1 pixel test image
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(self.test_image_path)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test directory
        shutil.rmtree(self.test_image_dir)
    
    def test_encode_image_base64(self):
        """Test encoding image as base64."""
        # Encode image
        result = ImageProcessor.encode_image_base64(str(self.test_image_path))
        
        # Check result structure
        self.assertEqual(result["type"], "image")
        self.assertEqual(result["source"]["type"], "base64")
        self.assertEqual(result["source"]["media_type"], "image/jpeg")
        self.assertTrue(isinstance(result["source"]["data"], str))
        
        # Check if data is valid base64
        try:
            decoded = base64.b64decode(result["source"]["data"])
            self.assertTrue(len(decoded) > 0)
        except Exception:
            self.fail("Invalid base64 data")
    
    def test_encode_image_url(self):
        """Test encoding image URL."""
        # Encode URL
        url = "https://example.com/image.jpg"
        result = ImageProcessor.encode_image_url(url)
        
        # Check result structure
        self.assertEqual(result["type"], "image")
        self.assertEqual(result["source"]["type"], "url")
        self.assertEqual(result["source"]["url"], url)
    
    def test_optimize_image(self):
        """Test image optimization."""
        # Optimize image
        optimized_path = ImageProcessor.optimize_image(str(self.test_image_path), max_size_mb=1.0)
        
        # Check if optimized image exists
        self.assertTrue(os.path.exists(optimized_path))
        
        # Check if optimized image is different from original
        if optimized_path != str(self.test_image_path):
            # Clean up optimized image
            os.unlink(optimized_path)

class TestImageTools(unittest.TestCase):
    """Test cases for image tools."""
    
    @patch('image_processing.ImageAnalyzer')
    def test_get_image_tools(self, mock_analyzer_class):
        """Test getting image tools."""
        # Mock analyzer
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Get image tools
        tools = get_image_tools()
        
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
            self.assertEqual(tool.category, 'image')