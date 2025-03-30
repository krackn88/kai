# Add to the RAGSystem class in rag.py

class RAGSystem:
    """Complete RAG system combining all components."""
    
    def __init__(self, storage_dir: str = "vector_store", embedding_model: str = "claude-3-sonnet-20240229"):
        """Initialize the RAG system."""
        self.vector_store = VectorStore(storage_dir)
        self.embedding_generator = EmbeddingGenerator(model=embedding_model)
        self.document_processor = DocumentProcessor(self.vector_store, self.embedding_generator)
        self.retriever = RAGRetriever(self.vector_store, self.embedding_generator)
        
        # Initialize enhanced components
        self.hybrid_searcher = HybridSearcher(self.vector_store)
        self.collection_manager = CollectionManager(storage_dir)
    
    async def add_document_from_file(self, file_path: str, metadata: Dict[str, Any] = None, 
                             chunk_strategy: str = "tokens", collection_name: Optional[str] = None) -> Document:
        """Add a document from a file to the RAG system."""
        # Process file with enhanced document processor
        text, extracted_metadata = DocumentProcessor.extract_text_from_file(file_path)
        
        # Combine extracted metadata with provided metadata
        combined_metadata = extracted_metadata
        if metadata:
            combined_metadata.update(metadata)
        
        # Add collection information if provided
        if collection_name:
            combined_metadata["collection"] = collection_name
            
            # Add to collection if it exists
            try:
                collection = self.collection_manager.get_collection(collection_name)
            except ValueError:
                collection = self.collection_manager.create_collection(collection_name)
        
        # Process document
        document = await self.add_document(text, combined_metadata, chunk_strategy)
        
        return document
    
    async def hybrid_query(self, query: str, top_k: int = 5, 
                    filters: Optional[Dict[str, Any]] = None, 
                    vector_weight: float = 0.7) -> Dict[str, Any]:
        """Query the RAG system using hybrid search."""
        # Perform hybrid search
        results = await self.hybrid_searcher.hybrid_search(query, top_k, vector_weight)
        
        # Apply filters if provided
        if filters:
            filtered_results = []
            for result in results:
                metadata = result["metadata"]
                
                # Check if all filter criteria match
                matches = True
                for key, value in filters.items():
                    if key not in metadata or metadata[key] != value:
                        matches = False
                        break
                
                if matches:
                    filtered_results.append(result)
            
            results = filtered_results
        
        return {
            "query": query,
            "results": results
        }
    
    async def get_hybrid_query_context(self, query: str, top_k: int = 5, 
                                filters: Optional[Dict[str, Any]] = None,
                                vector_weight: float = 0.7) -> str:
        """Get formatted context for a query to inject into a prompt using hybrid search."""
        results = await self.hybrid_query(query, top_k, filters, vector_weight)
        
        formatted_text = "RELEVANT CONTEXT:\n\n"
        
        for i, result in enumerate(results["results"]):
            formatted_text += f"[Document {i+1}] (Relevance: {result['score']:.4f})\n"
            formatted_text += f"{result['content']}\n\n"
        
        return formatted_text