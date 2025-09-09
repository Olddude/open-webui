# Open WebUI RAG and File Upload Guide

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [File Upload Features](#file-upload-features)
4. [RAG (Retrieval-Augmented Generation)](#rag-retrieval-augmented-generation)
5. [Agentic UI Features](#agentic-ui-features)
6. [API Integration](#api-integration)
7. [Troubleshooting](#troubleshooting)

## Overview

Open WebUI provides a comprehensive interface for interacting with LLMs, featuring advanced file upload capabilities and RAG (Retrieval-Augmented Generation) for context-aware responses. The system integrates with multiple backends including Ollama, OpenAI, and custom pipelines.

### Architecture

- **Frontend**: SvelteKit application running on port 5173
- **Backend**: FastAPI server running on port 8080
- **Database**: SQLite/PostgreSQL for persistence
- **Vector Store**: Qdrant for RAG embeddings (optional)
- **File Storage**: Local filesystem or S3-compatible storage

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11 or 3.12
- UV package manager (for Python dependencies)

### Starting the Services

#### Backend

```bash
cd backend
uv pip install -r requirements.txt
uv run python -m open_webui.main
# Backend will be available at http://localhost:8080
```

#### Frontend

```bash
npm install
npm run dev
# Frontend will be available at http://localhost:5173
```

### Default Credentials

- **First User**: Automatically becomes admin
- **Admin Panel**: Available at `/admin` route

## File Upload Features

### Supported File Types

#### Documents

- **PDF**: Full text extraction with OCR support
- **DOCX/DOC**: Microsoft Word documents
- **TXT**: Plain text files
- **Markdown**: `.md` files
- **CSV**: Comma-separated values
- **JSON**: Structured data files

#### Images

- **PNG, JPG, JPEG, GIF**: Direct vision model support
- **WebP, SVG**: Web formats
- OCR extraction for text in images

#### Code Files

- All programming language files
- Syntax highlighting in chat
- Code analysis capabilities

### How to Upload Files

#### Method 1: Drag and Drop

1. Open a chat conversation
2. Drag files directly into the chat input area
3. Files will appear as attachments
4. Send your message with the files attached

#### Method 2: File Picker

1. Click the paperclip icon (📎) in the chat input
2. Select files from your system
3. Multiple files can be selected at once
4. Files appear as chips above the input

#### Method 3: Knowledge Base Upload

1. Navigate to **Workspace** → **Knowledge**
2. Click **"+ Add Knowledge"**
3. Upload documents that will be indexed for RAG
4. Documents become searchable across all chats

### File Processing

#### Automatic Processing

- Text extraction from PDFs (including scanned documents via OCR)
- Content parsing from Office documents
- Image analysis for vision-capable models
- Automatic chunking for large documents

#### File Size Limits

- Default: 100MB per file
- Configurable in admin settings
- Large files are automatically chunked for processing

## RAG (Retrieval-Augmented Generation)

### Setting Up RAG

#### 1. Configure Embeddings

Navigate to **Settings** → **Documents** → **Embedding Model**

Options:

- **Local Embeddings**: Using Ollama

  ```bash
  # Install an embedding model in Ollama
  ollama pull nomic-embed-text
  ```

- **OpenAI Embeddings**: Configure API key
- **Custom Embeddings**: Via pipeline configuration

#### 2. Vector Database Setup

##### Using Qdrant (Recommended for Production)

```yaml
# Already configured in docker-compose.infra.yaml
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"
    - "6334:6334"
```

##### Using ChromaDB (Default)

- Automatically configured
- No additional setup required
- Data stored in `backend/data/vector_db`

### Using RAG in Conversations

#### Method 1: Global Knowledge Base

1. Upload documents to **Workspace** → **Knowledge**
2. Enable **"Search Knowledge"** in chat settings
3. Ask questions - relevant context will be automatically retrieved

#### Method 2: Conversation-Specific Documents

1. Upload documents directly in a chat
2. Documents are indexed for that conversation
3. Context is automatically included in responses

#### Method 3: Collections

1. Create document collections in **Workspace** → **Collections**
2. Organize related documents together
3. Select collections to search in chat settings

### RAG Configuration

#### Retrieval Settings

Access via **Settings** → **Documents**:

- **Chunk Size**: 1000 tokens (default)
- **Chunk Overlap**: 100 tokens
- **Top K Results**: 5 (number of chunks to retrieve)
- **Relevance Threshold**: 0.7 (minimum similarity score)

#### Advanced RAG Features

##### Hybrid Search

Combines vector similarity with keyword search:

```python
# Enabled by default
# Adjustable via API or admin panel
hybrid_search_alpha = 0.5  # Balance between vector and keyword
```

##### Reranking

Improves retrieval quality:

- **Cross-Encoder Reranking**: More accurate relevance scoring
- **MMR (Maximal Marginal Relevance)**: Diversity in results

## Agentic UI Features

The application now includes an agentic interface with reasoning and task planning capabilities visible across all views.

### Components

#### 1. Agent Panel (Left Sidebar)

- **Reasoning Display**: Shows the model's thinking process
- **Task Planning**: Breaks down complex requests into steps
- **Progress Tracking**: Visual indicators for task completion

#### 2. Main Chat Area (Center)

- Standard conversation interface
- File upload support
- Message history
- Code highlighting

#### 3. Artifacts Panel (Right Sidebar)

- Generated content display
- Code outputs
- Document previews
- Charts and visualizations

### Using the Agentic Features

#### Reasoning Mode

1. The agent shows its reasoning process in real-time
2. Visible thought chains for complex problem-solving
3. Step-by-step execution tracking

#### Task Planning

1. Complex requests are automatically broken into subtasks
2. Progress indicators show completion status
3. Ability to pause/resume task execution

### Customizing the Interface

#### Panel Visibility

- Drag to resize panels
- Click panel headers to collapse/expand
- Settings persist across sessions

#### Display Modes

- **Full Agentic**: All panels visible
- **Classic**: Chat-only view
- **Focused**: Hide sidebars for distraction-free chat

## API Integration

### File Upload via API

#### Upload to Knowledge Base

```python
import requests

# Upload a document
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/api/v1/files',
        files={'file': f},
        headers={'Authorization': 'Bearer YOUR_API_KEY'}
    )
    file_id = response.json()['id']

# Create knowledge entry
knowledge_response = requests.post(
    'http://localhost:8080/api/v1/knowledge',
    json={
        'name': 'My Document',
        'file_ids': [file_id],
        'collection_id': 'optional-collection-id'
    },
    headers={'Authorization': 'Bearer YOUR_API_KEY'}
)
```

#### Chat with File Context

```python
# Send message with file context
chat_response = requests.post(
    'http://localhost:8080/api/v1/chat/completions',
    json={
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'user',
                'content': 'Summarize this document',
                'files': [file_id]
            }
        ],
        'use_rag': True
    },
    headers={'Authorization': 'Bearer YOUR_API_KEY'}
)
```

### RAG Configuration via API

```python
# Configure RAG settings
rag_config = requests.put(
    'http://localhost:8080/api/v1/configs/rag',
    json={
        'chunk_size': 1000,
        'chunk_overlap': 100,
        'top_k': 5,
        'relevance_threshold': 0.7,
        'hybrid_search': True,
        'reranking': True
    },
    headers={'Authorization': 'Bearer YOUR_API_KEY'}
)
```

## Advanced Features

### Custom Pipelines

Create custom processing pipelines for specific document types:

```python
# workspace/functions/custom_rag_function.py
from typing import List, Dict
from pydantic import BaseModel

class Pipeline:
    def __init__(self):
        self.name = "Custom RAG Pipeline"
        
    async def process_document(self, document: Dict) -> List[Dict]:
        # Custom processing logic
        chunks = self.custom_chunking(document['content'])
        embeddings = await self.generate_embeddings(chunks)
        return embeddings
    
    def custom_chunking(self, content: str) -> List[str]:
        # Implement custom chunking strategy
        pass
    
    async def generate_embeddings(self, chunks: List[str]) -> List[Dict]:
        # Generate embeddings using preferred model
        pass
```

### Recipe RAG Pipeline Example

The repository includes a recipe-specific RAG pipeline that demonstrates:

- Structured data extraction from recipes
- Ingredient parsing and normalization
- Cooking instruction segmentation
- Nutrition information extraction
- OpenAI-powered recipe enhancement
- Agentic UI integration with reasoning and task planning

Location: `workspace/functions/recipe_rag_function.py`

#### Using the Recipe Pipeline

1. **Register the Pipeline**:
   - Navigate to Admin Panel → Pipelines
   - Upload `workspace/functions/recipe_rag_function.py`
   - The pipeline will be automatically loaded

2. **Trigger in Chat**:
   Use these keywords to activate the pipeline:
   - "Process recipe Excel file"
   - "Convert recipe data to JSON"
   - "Parse recipe from Excel"
   - "Recipe schema validation"

3. **Pipeline Features**:
   - Automatic Excel file processing
   - Schema validation
   - OpenAI enhancement (with API key)
   - Progress tracking in UI
   - JSON output generation

See `PIPELINE_DEBUG_GUIDE.md` for debugging instructions.

### Function Calling with RAG

Enable function calling to process documents dynamically:

```python
# workspace/functions/document_analyzer.py
def analyze_document(file_path: str, analysis_type: str = "summary"):
    """
    Analyze uploaded documents with specific processing
    """
    if analysis_type == "summary":
        return generate_summary(file_path)
    elif analysis_type == "extract_data":
        return extract_structured_data(file_path)
    elif analysis_type == "translate":
        return translate_document(file_path)
```

## Troubleshooting

### Common Issues

#### 1. File Upload Fails

- **Check file size**: Ensure it's under the configured limit
- **Verify file type**: Check supported formats list
- **Storage permissions**: Ensure `backend/data/uploads` is writable
- **API limits**: Check rate limiting settings

#### 2. RAG Not Finding Relevant Content

- **Embedding model**: Ensure it's properly configured
- **Chunk size**: Try adjusting for your document types
- **Relevance threshold**: Lower for more results
- **Index status**: Check if documents are properly indexed

#### 3. Slow Processing

- **Vector database**: Consider using Qdrant for better performance
- **Embedding batch size**: Increase for faster processing
- **Document preprocessing**: Enable caching in settings

### Debugging

#### Enable Debug Logging

```bash
# Backend
export LOG_LEVEL=DEBUG
uv run python -m open_webui.main

# Frontend
npm run dev -- --debug
```

#### Check Processing Status

```python
# Via API
status = requests.get(
    f'http://localhost:8080/api/v1/files/{file_id}/status',
    headers={'Authorization': 'Bearer YOUR_API_KEY'}
)
print(status.json())
```

#### Monitor Vector Database

- Qdrant Dashboard: <http://localhost:6333/dashboard>
- Check collection statistics
- Verify point count matches uploaded documents

### Performance Optimization

#### 1. Batch Processing

- Upload multiple files simultaneously
- Process in background jobs
- Use collection uploads for related documents

#### 2. Caching

- Enable embedding cache in settings
- Configure Redis for session caching
- Use CDN for static file serving

#### 3. Model Selection

- Use appropriate embedding models for your language
- Balance between quality and speed
- Consider specialized models for specific domains

## Best Practices

### Document Preparation

1. **Clean text**: Remove unnecessary formatting
2. **Structured data**: Use JSON/CSV for tabular data
3. **Metadata**: Include relevant metadata in filenames
4. **Language**: Separate documents by language

### RAG Optimization

1. **Chunk strategically**: Adjust size based on content type
2. **Test retrieval**: Verify quality with sample queries
3. **Monitor usage**: Track token consumption
4. **Update regularly**: Refresh embeddings as needed

### Security

1. **File validation**: Scan uploads for malicious content
2. **Access control**: Use collections for team segregation
3. **API keys**: Rotate regularly
4. **Data privacy**: Configure local processing when required

## Additional Resources

- **API Documentation**: <http://localhost:8080/docs>
- **OpenAPI Specification**: <http://localhost:8080/openapi.json> (Full API schema for integration)
- **Frontend Application**: <http://localhost:5173>
- **Community Discord**: [Join Discord](https://discord.gg/openwebui)
- **GitHub Issues**: [Report Issues](https://github.com/open-webui/open-webui/issues)

## Support

For additional help:

1. Check the [official documentation](https://docs.openwebui.com)
2. Search [existing issues](https://github.com/open-webui/open-webui/issues)
3. Join the community Discord
4. Contact support (enterprise users)

---

*Last updated: 2025-01-09*
*Version: Based on latest main branch*
