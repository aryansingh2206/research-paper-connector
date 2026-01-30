# System Architecture Documentation

## Overview

The Research Paper Idea Connector is built as a modular, production-grade system with clear separation of concerns. This document details the architecture, data flows, and design decisions.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                              │
│                                                                 │
│  ┌─────────────────┐              ┌─────────────────┐         │
│  │  Web Interface  │              │   CLI Tools     │         │
│  │  (Streamlit)    │              │   (Scripts)     │         │
│  └────────┬────────┘              └────────┬────────┘         │
│           │                                 │                   │
└───────────┼─────────────────────────────────┼───────────────────┘
            │                                 │
┌───────────┼─────────────────────────────────┼───────────────────┐
│           │        APPLICATION LAYER        │                   │
│           │                                 │                   │
│  ┌────────▼────────┐  ┌────────────┐  ┌───▼──────────┐        │
│  │   Search        │  │ Ingestion  │  │   Document   │        │
│  │   Engine        │  │ Pipeline   │  │   Processor  │        │
│  └────────┬────────┘  └─────┬──────┘  └──────┬───────┘        │
│           │                  │                 │                │
│  ┌────────▼──────────────────▼─────────────────▼──────┐        │
│  │            Embedding Model Layer                    │        │
│  │        (sentence-transformers)                      │        │
│  └────────┬───────────────────────────────────┬────────┘        │
│           │                                    │                │
└───────────┼────────────────────────────────────┼────────────────┘
            │                                    │
┌───────────┼────────────────────────────────────┼────────────────┐
│           │         DATA LAYER                 │                │
│           │                                    │                │
│  ┌────────▼────────────────────────────────────▼──────┐        │
│  │              Endee Client Wrapper                  │        │
│  │           (HTTP API Communication)                 │        │
│  └────────┬───────────────────────────────────────────┘        │
│           │                                                     │
│  ┌────────▼───────────────────────────────────────────┐        │
│  │          ENDEE VECTOR DATABASE                     │        │
│  │  • Collections: research_papers                    │        │
│  │  • Vectors: 384-dimensional embeddings             │        │
│  │  • Metadata: paper_id, title, chunk_text, etc.    │        │
│  │  • Operations: insert, search, retrieve            │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. User Layer

#### Web Interface (Streamlit)
- **Purpose**: Primary user interface for non-technical users
- **Features**:
  - File upload (PDF/TXT)
  - Search interface with multiple modes
  - Results visualization
  - Configuration management
- **Technology**: Streamlit framework
- **Port**: 8501

#### CLI Tools
- **Purpose**: Automation and batch operations
- **Scripts**:
  - `ingest_papers.py`: Batch paper ingestion
  - `query_system.py`: Command-line search
  - `setup_verify.py`: System verification
- **Use Cases**: DevOps, automation, scripting

---

### 2. Application Layer

#### Document Processor (`document_processor.py`)
**Responsibilities:**
- PDF text extraction (PyPDF2)
- Text cleaning and normalization
- Paragraph-level chunking
- Metadata attachment

**Key Methods:**
```python
extract_text(file_path) -> str
split_into_chunks(text) -> List[str]
process_document(file_path, paper_id, metadata) -> List[DocumentChunk]
```

**Design Decisions:**
- Paragraph-based chunking (vs. fixed-size) for semantic coherence
- Configurable chunk size via environment
- Preserves source metadata for traceability

#### Embedding Model Layer (`embeddings.py`)
**Responsibilities:**
- Load sentence-transformer model
- Generate embeddings for text
- Batch processing for efficiency
- Similarity computation

**Model Choice:**
- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Dimension**: 384
- **Why**: Balance of quality, speed, and size

**Key Methods:**
```python
embed_text(text: str) -> List[float]
embed_batch(texts: List[str]) -> List[List[float]]
compute_similarity(emb1, emb2) -> float
```

#### Ingestion Pipeline (`ingestion.py`)
**Responsibilities:**
- Orchestrates document processing
- Coordinates embedding generation
- Manages Endee storage
- Error handling and reporting

**Pipeline Steps:**
1. Document validation
2. Text extraction and chunking
3. Batch embedding generation
4. Vector document creation
5. Endee storage via HTTP
6. Status reporting

**Key Features:**
- Batch processing for efficiency
- Transaction-like behavior (all-or-nothing per paper)
- Comprehensive error handling
- Progress tracking

#### Search Engine (`search_engine.py`)
**Responsibilities:**
- Query processing
- Endee search orchestration
- Result ranking and filtering
- Result formatting

**Search Modes:**
1. **Semantic Search**: Natural language queries
2. **Related Papers**: Find similar papers
3. **Contradiction Detection**: Identify conflicting findings

**Key Methods:**
```python
search(query, top_k, filters) -> List[SearchMatch]
find_related_papers(paper_id) -> List[SearchMatch]
find_contradictions(query) -> List[SearchMatch]
```

#### LLM Summarizer (`llm_summarizer.py`)
**Responsibilities:**
- Optional LLM integration
- Result summarization
- Contradiction analysis
- Multi-provider support (OpenAI, Anthropic)

**Design**: Completely optional - system works without it

---

### 3. Data Layer

#### Endee Client (`endee_client.py`)
**Responsibilities:**
- HTTP API wrapper for Endee
- Collection management
- Vector CRUD operations
- Error handling and retries

**API Operations:**
```python
create_collection(dimension, metric) -> bool
insert_vectors(documents: List[VectorDocument]) -> bool
search(query_vector, top_k, filters) -> List[SearchResult]
get_vector(vector_id) -> Dict
delete_collection() -> bool
```

**Design Patterns:**
- HTTP client with connection pooling
- Automatic retry logic
- Type-safe interfaces (dataclasses)
- Comprehensive logging

#### Endee Vector Database
**Role**: Core data store for vector search

**Schema:**
```
Collection: research_papers
├── Dimension: 384
├── Metric: cosine
└── Vectors:
    ├── id: "paper_001_chunk_0"
    ├── vector: [0.234, -0.456, ...]
    └── metadata:
        ├── paper_id: "paper_001"
        ├── title: "Paper Title"
        ├── authors: "Smith et al."
        ├── chunk_index: 0
        ├── chunk_text: "Full paragraph text..."
        └── [other metadata]
```

**Why Endee?**
- Native vector similarity search
- RESTful HTTP API (language-agnostic)
- Lightweight and fast
- Docker-based deployment
- Open source and extensible

---

## Data Flows

### Ingestion Flow

```
User uploads PDF
    │
    ▼
┌─────────────────────┐
│ Document Processor  │
│ • Extract text      │
│ • Clean text        │
│ • Split into chunks │
└──────────┬──────────┘
           │
           ▼ List[text_chunks]
┌─────────────────────┐
│ Embedding Model     │
│ • Batch encode      │
│ • Generate vectors  │
└──────────┬──────────┘
           │
           ▼ List[vectors]
┌─────────────────────┐
│ Ingestion Pipeline  │
│ • Create VectorDocs │
│ • Add metadata      │
└──────────┬──────────┘
           │
           ▼ VectorDocument[]
┌─────────────────────┐
│ Endee Client        │
│ • HTTP POST         │
│ • /collections/X/   │
│   vectors           │
└──────────┬──────────┘
           │
           ▼
     ┌─────────┐
     │  Endee  │
     │ Storage │
     └─────────┘
```

### Query Flow

```
User enters query
    │
    ▼
┌─────────────────────┐
│ Search Engine       │
│ • Validate query    │
└──────────┬──────────┘
           │
           ▼ query_text
┌─────────────────────┐
│ Embedding Model     │
│ • Encode query      │
└──────────┬──────────┘
           │
           ▼ query_vector
┌─────────────────────┐
│ Endee Client        │
│ • HTTP POST         │
│ • /collections/X/   │
│   search            │
└──────────┬──────────┘
           │
           ▼
     ┌─────────┐
     │  Endee  │
     │ Cosine  │
     │ Search  │
     └────┬────┘
          │
          ▼ similar_vectors
┌─────────────────────┐
│ Search Engine       │
│ • Filter results    │
│ • Rank by score     │
│ • Format output     │
└──────────┬──────────┘
           │
           ▼
    Display to User
```

---

## Technology Decisions

### Why Sentence-Transformers?
**Alternatives Considered**: OpenAI Embeddings, Cohere, Universal Sentence Encoder

**Decision**: sentence-transformers/all-MiniLM-L6-v2

**Rationale**:
- ✅ Open source and free
- ✅ Runs locally (no API dependencies)
- ✅ Fast inference (CPU-friendly)
- ✅ Good quality for research text
- ✅ 384 dimensions (vs 1536 for OpenAI) - more efficient
- ✅ Well-documented and maintained

### Why Endee?
**Alternatives Considered**: Pinecone, Weaviate, Milvus, ChromaDB, Qdrant

**Decision**: Endee

**Rationale**:
- ✅ Lightweight and simple
- ✅ RESTful HTTP API (easy integration)
- ✅ Docker-based deployment
- ✅ No cloud lock-in
- ✅ Perfect for research/evaluation projects
- ✅ Open source

### Why Streamlit?
**Alternatives Considered**: FastAPI + React, Gradio, Flask

**Decision**: Streamlit

**Rationale**:
- ✅ Rapid development
- ✅ Python-native (no frontend expertise needed)
- ✅ Built-in components for ML apps
- ✅ Auto-reload during development
- ✅ Easy deployment

### Why Docker Compose?
**Alternatives Considered**: Kubernetes, Docker Swarm, manual setup

**Decision**: Docker Compose

**Rationale**:
- ✅ Simple orchestration
- ✅ Perfect for evaluation/demo
- ✅ Reproducible setup
- ✅ Easy to understand
- ✅ Works on all platforms

---

## Scalability Considerations

### Current Design
- **Scale**: 1,000-10,000 papers
- **Performance**: Sub-second search
- **Resources**: 4GB RAM, 2 CPU cores

### Scaling Up (10K-100K papers)

**Optimizations Needed**:
1. **Embedding caching**: Cache frequently accessed embeddings
2. **Endee optimization**: Tune indexing parameters
3. **Batch size tuning**: Adjust for available memory
4. **Connection pooling**: Increase HTTP client connections

**Infrastructure**:
- More RAM (8-16GB)
- SSD storage for Endee
- Optional: GPU for embedding generation

### Scaling Out (100K+ papers)

**Architecture Changes**:
1. **Distributed Endee**: Multiple Endee instances with sharding
2. **Queue system**: RabbitMQ/Redis for async ingestion
3. **Load balancer**: Nginx/HAProxy for web tier
4. **Object storage**: S3/MinIO for PDFs
5. **Cache layer**: Redis for query results

---

## Security Considerations

### Current Implementation
- Local deployment (no external exposure by default)
- No authentication (suitable for single-user/evaluation)
- API keys stored in environment variables

### Production Recommendations
1. **Authentication**: Add user authentication (OAuth, JWT)
2. **HTTPS**: SSL/TLS for all connections
3. **API key management**: Use secrets manager
4. **Rate limiting**: Prevent abuse
5. **Input validation**: Sanitize all user inputs
6. **CORS**: Configure properly for web deployment

---

## Error Handling Strategy

### Levels of Error Handling

1. **Component Level**: Try-catch in individual methods
2. **Pipeline Level**: Transaction-like rollback for ingestion
3. **API Level**: HTTP error codes and messages
4. **UI Level**: User-friendly error messages

### Example: Ingestion Error Flow
```
PDF extraction fails
    ↓
Exception caught in document_processor
    ↓
Log error with traceback
    ↓
Return empty chunks
    ↓
Ingestion pipeline detects empty chunks
    ↓
Skip this paper, continue with others
    ↓
Report failure in final status
    ↓
User sees: "❌ paper.pdf failed - could not extract text"
```

---

## Testing Strategy

### Unit Tests
- Individual component testing
- Mock external dependencies (Endee)
- Focus on business logic

### Integration Tests
- Full pipeline testing
- Real Endee instance
- End-to-end workflows

### Manual Testing
- Web interface smoke tests
- CLI command validation
- Performance benchmarks

---

## Deployment Options

### 1. Local Development
```bash
docker-compose up -d
```

### 2. Single Server
```bash
# Production docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Cloud Deployment
- **AWS**: ECS + ECR + RDS
- **GCP**: Cloud Run + Container Registry
- **Azure**: Container Instances

### 4. On-Premise
- Install Docker on server
- Mount persistent volumes
- Configure firewall rules

---

## Monitoring and Observability

### Logs
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log aggregation (ELK stack, Grafana Loki)

### Metrics
- Ingestion throughput (papers/hour)
- Query latency (p50, p95, p99)
- Endee performance (index size, query time)
- Resource usage (CPU, memory, disk)

### Health Checks
- Endee `/health` endpoint
- Embedding model loading status
- Streamlit application health

---

## Future Architecture Evolution

### Phase 1 (Current)
- Single-server deployment
- Local vector database
- Basic search functionality

### Phase 2 (Improvements)
- Distributed Endee
- Advanced filters (date, domain, citations)
- Citation graph analysis
- Multi-modal support (images, equations)

### Phase 3 (Scale)
- Microservices architecture
- Kubernetes orchestration
- Real-time collaboration
- API marketplace

---

## Conclusion

The Research Paper Idea Connector is designed as a production-grade, modular system with:
- Clear separation of concerns
- Strong type safety
- Comprehensive error handling
- Scalability considerations
- Extensibility for future features

The architecture prioritizes:
1. **Simplicity**: Easy to understand and modify
2. **Reliability**: Robust error handling
3. **Performance**: Optimized for research use cases
4. **Maintainability**: Clean code, good documentation
5. **Evaluability**: Easy to set up and test

**Core Innovation**: Using Endee vector database for semantic paper discovery at paragraph-level granularity, enabling discovery of conceptual overlaps and contradictions across research domains.
