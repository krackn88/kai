"""
Unit tests for RAG system
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import MagicMock, patch
from pathlib import Path
import json

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag import RAGSystem, Document, VectorStore, EmbeddingGenerator
from rag_enhancements import DocumentProcessor, HybridSearcher, DocumentCollection, CollectionManager

class TestVectorStore(unittest.TestCase):
    """Test cases for the VectorStore class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test directory
        self.test_dir = Path(tempfile.mkdtemp())
        self.vector_store = VectorStore(str(self.test_dir))
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test directory
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test VectorStore initialization."""
        self.assertEqual(self.vector_store.storage_dir, self.test_dir)
        self.assertEqual(self.vector_store.documents_dir, self.test_dir / "documents")
        self.assertEqual(self.vector_store.chunks_dir, self.test_dir / "chunks")
        self.assertTrue(self.vector_store.documents_dir.exists())
        self.assertTrue(self.vector_store.chunks_dir.exists())
    
    def test_save_and_get_document(self):
        """Test saving and retrieving a document."""
        # Create a test document
        doc = Document(
            id="test123",
            content="This is a test document.",
            metadata={"source": "test"},
            chunks=[]
        )
        
        # Save document
        self.vector_store.save_document(doc)
        
        # Check if document file exists
        doc_path = self.vector_store.documents_dir / "test123.json"
        self.assertTrue(doc_path.exists())
        
        # Get document
        retrieved_doc = self.vector_store.get_document("test123")
        
        # Check if retrieved document is correct
        self.assertEqual(retrieved_doc.id, "test123")
        self.assertEqual(retrieved_doc.content, "This is a test document.")
        self.assertEqual(retrieved_doc.metadata["source"], "test")
    
    def test_delete_document(self):
        """Test deleting a document."""
        # Create a test document
        doc = Document(
            id="test123",
            content="This is a test document.",
            metadata={"source": "test"},
            chunks=[]
        )
        
        # Save document
        self.vector_store.save_document(doc)
        
        # Delete document
        result = self.vector_store.delete_document("test123")
        
        # Check if deletion was successful
        self.assertTrue(result)
        
        # Check if document file is deleted
        doc_path = self.vector_store.documents_dir / "test123.json"
        self.assertFalse(doc_path.exists())
        
        # Try to get deleted document
        retrieved_doc = self.vector_store.get_document("test123")
        self.assertIsNone(retrieved_doc)
    
    def test_get_nonexistent_document(self):
        """Test getting a non-existent document."""
        # Try to get non-existent document
        retrieved_doc = self.vector_store.get_document("nonexistent")
        self.assertIsNone(retrieved_doc)

class TestDocumentProcessor(unittest.TestCase):
    """Test cases for the DocumentProcessor class from rag_enhancements."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test directory
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create test files
        self.test_txt_path = self.test_dir / "test.txt"
        with open(self.test_txt_path, 'w') as f:
            f.write("This is a test text file.\nIt has multiple lines.")
        
        self.test_html_path = self.test_dir / "test.html"
        with open(self.test_html_path, 'w') as f:
            f.write("<html><body><h1>Test HTML</h1><p>This is a test paragraph.</p></body></html>")
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test directory
        shutil.rmtree(self.test_dir)
    
    def test_extract_text_from_file_txt(self):
        """Test extracting text from a text file."""
        # Extract text
        text, metadata = DocumentProcessor.extract_text_from_file(str(self.test_txt_path))
        
        # Check if text is correct
        self.assertEqual(text, "This is a test text file.\nIt has multiple lines.")
        
        # Check if metadata is correct
        self.assertEqual(metadata["filename"], "test.txt")
        self.assertEqual(metadata["extension"], ".txt")
        self.assertEqual(metadata["type"], "text")
        self.assertTrue("size_bytes" in metadata)
        self.assertTrue("last_modified" in metadata)
        self.assertTrue("processed_at" in metadata)
        self.assertTrue("word_count" in metadata)
        self.assertTrue("char_count" in metadata)
    
    def test_extract_text_from_file_html(self):
        """Test extracting text from an HTML file."""
        # Extract text
        text, metadata = DocumentProcessor.extract_text_from_file(str(self.test_html_path))
        
        # Check if text is correct (ignoring whitespace differences)
        self.assertIn("Test HTML", text)
        self.assertIn("This is a test paragraph", text)
        
        # Check if metadata is correct
        self.assertEqual(metadata["filename"], "test.html")
        self.assertEqual(metadata["extension"], ".html")
        self.assertEqual(metadata["type"], "html")
        self.assertTrue("size_bytes" in metadata)
        self.assertTrue("last_modified" in metadata)
        self.assertTrue("processed_at" in metadata)
        self.assertTrue("word_count" in metadata)
        self.assertTrue("char_count" in metadata)

class TestCollectionManager(unittest.TestCase):
    """Test cases for the CollectionManager class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test directory
        self.test_dir = Path(tempfile.mkdtemp())
        self.collection_manager = CollectionManager(str(self.test_dir))
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test directory
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test CollectionManager initialization."""
        self.assertEqual(self.collection_manager.storage_dir, self.test_dir)
        self.assertIn("default", self.collection_manager.collections)
        self.assertEqual(self.collection_manager.metadata["default_collection"], "default")
    
    def test_create_collection(self):
        """Test creating a collection."""
        # Create a new collection
        collection = self.collection_manager.create_collection("test_collection")
        
        # Check if collection was created
        self.assertIn("test_collection", self.collection_manager.collections)
        self.assertIn("test_collection", self.collection_manager.metadata["collections"])
        
        # Check if collection directory exists
        collection_dir = self.test_dir / "test_collection"
        self.assertTrue(collection_dir.exists())
        
        # Check if collection metadata file exists
        metadata_path = collection_dir / "metadata.json"
        self.assertTrue(metadata_path.exists())
    
    def test_get_collection(self):
        """Test getting a collection."""
        # Create a new collection
        self.collection_manager.create_collection("test_collection")
        
        # Get collection
        collection = self.collection_manager.get_collection("test_collection")
        
        # Check if collection is correct
        self.assertEqual(collection.name, "test_collection")
        self.assertEqual(collection.storage_dir, self.test_dir / "test_collection")
    
    def test_delete_collection(self):
        """Test deleting a collection."""
        # Create a new collection
        self.collection_manager.create_collection("test_collection")
        
        # Delete collection
        result = self.collection_manager.delete_collection("test_collection")
        
        # Check if deletion was successful
        self.assertTrue(result)
        
        # Check if collection was removed
        self.assertNotIn("test_collection", self.collection_manager.collections)
        self.assertNotIn("test_collection", self.collection_manager.metadata["collections"])
        
        # Check if collection directory was removed
        collection_dir = self.test_dir / "test_collection"
        self.assertFalse(collection_dir.exists())
    
    def test_list_collections(self):
        """Test listing collections."""
        # Create new collections
        self.collection_manager.create_collection("test_collection1")
        self.collection_manager.create_collection("test_collection2")
        
        # List collections
        collections = self.collection_manager.list_collections()
        
        # Check if collections list is correct
        self.assertEqual(len(collections), 3)  # default + 2 new collections
        
        collection_names = [c["name"] for c in collections]
        self.assertIn("default", collection_names)
        self.assertIn("test_collection1", collection_names)
        self.assertIn("test_collection2", collection_names)