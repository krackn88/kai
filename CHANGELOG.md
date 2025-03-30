# Changelog

All notable changes to this project will be documented in this file.

## [1.7.0] - 2025-03-28

### Added
- Enhanced RAG capabilities
  - Support for multiple document formats (PDF, DOCX, Excel, CSV, HTML)
  - Document collection management with namespaces
  - Hybrid search combining vector and keyword search
  - Metadata filters for search queries
- FastAPI web backend with comprehensive API
  - REST endpoints for all agent capabilities
  - WebSocket support for streaming responses
  - File upload handling for images and documents
  - Authentication with API keys
- Initial test suite implementation
  - Unit tests for core agent functionality
  - Test utilities and mocking framework

### Changed
- Improved RAG system architecture with modular design
- Enhanced error handling and logging across all components
- Updated tool registration to support collection-based RAG

## [1.6.0] - 2025-03-27

### Added
- Web API foundation with FastAPI
  - Core API endpoints for agent communication
  - Conversation management
  - Tool execution
  - RAG integration
  - Image processing

### Changed
- Refactored agent components for better API integration
- Updated image processing to support web API uploads
- Enhanced response streaming for real-time UI updates

## [1.5.0] - 2025-03-27

### Added
- Support for image inputs with Claude 3 models
  - Image processing utilities for encoding and optimization
  - Image analysis tools using Claude's multimodal capabilities
  - OCR (text extraction) from images
  - Image description and detailed analysis
  - Image downloading and management
- CLI commands for image operations:
  - `image analyze` - Analyze images with custom prompts
  - `image ocr` - Extract text from images
  - `image describe` - Generate image descriptions
  - `image optimize` - Resize and compress images for Claude
  - `image download` - Download images from URLs
  - `image send` - Send messages with images
- Command-line options for image analysis:
  - `--image` - Specify image file to analyze
  - `--image-prompt` - Custom prompt for image analysis

### Changed
- Updated `Agent` class with multimodal input handling
- Enhanced CLI interface with image commands
- Improved main.py with image-specific command-line options

## [1.4.0] - 2025-03-27

### Added
- Retrieval-Augmented Generation (RAG) system
  - Vector store for document embeddings
  - Document processing and chunking strategies
  - Embedding generation using Claude API
  - Retrieval mechanisms and context injection
  - RAG integration with agent responses
- RAG command-line interface
  - Document management (add, delete, list)
  - RAG system querying
  - Statistics and reporting
- RAG tools for the agent
  - Document addition and retrieval
  - Context enhancement for queries
  - Metadata filtering and search
- Command-line options for RAG operations

### Changed
- Updated `Agent` class to support RAG context enhancement
- Improved CLI with RAG command support
- Enhanced main.py with command-line options for RAG

## [1.3.0] - 2025-03-27

### Added
- JSON mode support for structured outputs from Claude
- Predefined schemas for common outputs (text analysis, code analysis, etc.)
- Structured output CLI commands:
  - `structured list` - List available schemas
  - `structured analyze` - Process query with structured output
  - `structured custom` - Create and use custom schemas
- Command-line options for structured output processing
- Custom schema creation capabilities
- Enhanced anthropic_cookbook with structured output tools

### Changed
- Updated `Agent` class with methods for structured responses
- Improved CLI to support working with structured data
- Enhanced error handling for JSON parsing and validation

## [1.2.0] - 2025-03-27

### Added
- Model configuration and selection system with detailed model information
- Usage tracking and cost estimation for Claude API calls
- Model recommendation system based on task descriptions
- New CLI commands for model management:
  - `models list` - List all available models
  - `models info` - Show detailed model information
  - `models recommend` - Get model recommendations for tasks
  - `models current` - Show current model information
- `usage` command to show API usage statistics and costs
- Enhanced conversation saving with model information and usage stats

## [1.1.0] - 2025-03-27

### Added
- Streaming response capability for more responsive conversation
- Command-line argument support for model selection and streaming configuration
- `streaming` command to toggle streaming mode in CLI
- Enhanced error handling for streaming responses

### Changed
- Updated `Agent` class to support both streaming and non-streaming responses
- Modified CLI to display streamed responses in real-time
- Improved tool execution feedback during streaming

## [1.0.0] - 2025-03-27

### Added
- Initial release of the Anthropic-powered Agent with GitHub integration
- Core agent implementation with memory system and tool execution
- GitHub integration tools (repository info, code analysis, issue management)
- Claude-powered language tools (summarization, translation, code completion)
- System utility tools (file operations, data analysis, command execution)
- Advanced techniques from Anthropic's cookbook
- Command-line interface for interacting with the agent
- Comprehensive error handling and validation

## Technical Details

### Core Components
- `anthropic_agent.py`: Core agent implementation with tool execution framework
- `github_tools.py`: GitHub API integration for repository and code operations
- `claude_tools.py`: Claude-powered language capabilities
- `system_tools.py`: System and utility functions for file/data operations
- `anthropic_cookbook.py`: Advanced Claude capabilities from Anthropic's cookbook
- `agent_cli.py`: Command-line interface for interacting with the agent
- `main.py`: Main entry point with setup and configuration
- `model_config.py`: Model configuration, recommendation, and cost tracking
- `structured_schemas.py`: Predefined schemas for structured outputs
- `rag.py`: Retrieval-Augmented Generation system
- `rag_cli.py`: Command-line interface for RAG management
- `image_processing.py`: Image processing and analysis with Claude 3
- `web_api.py`: FastAPI backend for web interface
- `rag_enhancements.py`: Enhanced RAG capabilities for multiple formats
- `requirements.txt`: Required dependencies

### Key Features
- Conversation memory with context retention
- Tool execution with parameter validation
- GitHub repository exploration and code analysis
- Text summarization and translation using Claude
- Code completion and explanation
- File system operations with safety measures
- Data analysis and visualization tools
- Advanced prompting techniques (few-shot learning, chain-of-thought, etc.)
- Command-line interface with tool execution capabilities
- Streaming responses for responsive interaction
- Model selection and recommendation system
- Usage tracking and cost estimation
- Structured outputs with JSON mode
- Retrieval-Augmented Generation for knowledge enhancement
- Image analysis and multimodal capabilities
- Web API with REST endpoints and WebSocket support
- Enhanced RAG with multiple document formats and hybrid search